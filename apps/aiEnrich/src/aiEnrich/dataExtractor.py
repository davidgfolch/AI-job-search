import sys
import time

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.ai_helpers import (
    footer,
    mapJob,
    validateResult,
    RETRY_ERROR_PREFIX,
    MAX_AI_ENRICH_ERROR_LEN,
)
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger, job_log_context
from .aiEnrich_config import (
    get_job_enabled, get_ollama_base_url, get_timeout_job, get_model, get_max_ollama_failures,
    get_max_validation_retries, get_backend, get_openrouter_base_url, get_openrouter_model,
    get_openrouter_fallback_model,
)
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.ollama_client import query_ollama, resolve_ollama_url
from .extraction_contract import COMPANY_SCHEMA, EXTRACTION_SCHEMA, build_extraction_prompt, query_and_parse
from .openrouter_client import query_openrouter, ping_openrouter
from .companyExtractor import resolve_unspecified_company

logger = get_logger("aiEnrich.dataExtractor")
collector = MetricsCollector()

_resolved_ollama_url: str | None = None


def _get_ollama_base_url() -> str:
    return _resolved_ollama_url or get_ollama_base_url()


def _query_job(prompt: str, backend: str, model: str, response_schema: dict | None = None):
    if backend == "openrouter":
        return query_openrouter(
            prompt=prompt, model=model, base_url=get_openrouter_base_url(), timeout=get_timeout_job(), json_mode=False,
            fallback_model=get_openrouter_fallback_model(),
        )
    return query_ollama(
        prompt=prompt, model=model, primary_url=_get_ollama_base_url(), timeout=get_timeout_job(), json_mode=True,
        response_schema=response_schema or EXTRACTION_SCHEMA, return_metadata=True, log=logger,
    )


def _query_company(prompt: str, backend: str, model: str):
    """Company-only request, constrained with COMPANY_SCHEMA.

    EXTRACTION_SCHEMA must never be reused here: Ollama grammar-constrains the reply to it and its
    additionalProperties=false forbids `company`, so every response failed with "missing fields: company".
    """
    return _query_job(prompt, backend, model, COMPANY_SCHEMA)


def ping_backend() -> bool:
    global _resolved_ollama_url
    if get_backend() == "openrouter":
        return ping_openrouter(base_url=get_openrouter_base_url())
    _resolved_ollama_url = resolve_ollama_url(primary_url=get_ollama_base_url(), log=logger)
    return _resolved_ollama_url is not None


def _check_backend_available() -> bool:
    global ollama_consecutive_failures
    if ping_backend():
        ollama_consecutive_failures = 0
        return True
    ollama_consecutive_failures += 1
    max_failures = get_max_ollama_failures()
    logger.error("ai.unreachable", backend=get_backend(), consecutive_failures=ollama_consecutive_failures, max_failures=max_failures)
    if ollama_consecutive_failures >= max_failures:
        logger.critical("ai.exit_threshold_reached", consecutive_failures=ollama_consecutive_failures)
        sys.exit(1)
    return False


DEBUG = False

stopWatch = StopWatch()
totalCount = 0
total = 0
jobErrors = set[tuple[int, str]]()
ollama_consecutive_failures = 0
_batch_start = 0.0


def dataExtractor() -> int:
    global totalCount, jobErrors, _batch_start
    if not get_job_enabled():
        return 0
    if not _check_backend_available():
        return -1
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        total = repo.count_pending_enrichment()
        if total is None or total == 0:
            return 0
        logger.info("jobs.found", total=total)
        collector.set_pending("aiEnrich", total)
        stopWatch.start()
        _batch_start = time.time()
        for idx, id in enumerate(_getJobIdsList(repo)):
            _process_job_safe(repo, id, total, idx, "enrich")
        return total


def retry_failed_jobs() -> int:
    global totalCount, jobErrors, _batch_start
    if not get_job_enabled():
        return 0
    if not _check_backend_available():
        return -1
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        error_id = repo.get_enrichment_error_id_retry()
        if error_id is None:
            return 0
        logger.info("job.retry", job_id=error_id)
        stopWatch.start()
        _batch_start = time.time()
        _process_job_safe(repo, error_id, 1, 0, "retry")
        return 1


def _process_job_safe(
    repo: AiEnrichRepository,
    id: int,
    total: int,
    idx: int,
    process_name: str,
):
    global totalCount, jobErrors
    start_time = time.time()
    success = False
    title, company = "Unknown", "Unknown"
    try:
        with job_log_context(id):
            job = repo.get_job_to_enrich(id) if process_name == "enrich" else repo.get_job_to_retry(id)
            if job is None:
                logger.warning("job.not_found", job_id=id)
                return
            title, company = "Unknown", "Unknown"
            title, company, markdown = mapJob(job)
            try:
                backend = get_backend()
                model = get_openrouter_model() if backend == "openrouter" else get_model()
                logger.info("job.started", job_id=id, title=title, company=company, input_len=len(markdown), total=total, index=idx + 1, backend=backend, model=model)
                prompt = build_extraction_prompt(title, markdown)
                result, response = query_and_parse(
                    lambda retry_prompt: _query_job(retry_prompt, backend, model), prompt,
                    max_attempts=get_max_validation_retries() + 1, log=logger,
                )
                if response is None:
                    logger.warning("job.skipped_ai_unreachable", job_id=id, title=title, company=company)
                else:
                    if result is not None:
                        _save(repo, id, result)
                        success = True
                        resolve_unspecified_company(repo, id, title, company, markdown, lambda p: _query_company(p, backend, model), log=logger)
                    logger.info(
                        "job.result", job_id=id, result=result, duration=round(time.time() - start_time, 3), backend=backend,
                        model=model, done_reason=getattr(response, "done_reason", None),
                    )
            except (Exception, KeyboardInterrupt) as ex:
                _handle_error(repo, id, title, company, ex, process_name)
    except Exception as e:
        logger.error("job.critical_error", job_id=id, error=str(e))
    totalCount += 1
    duration = time.time() - start_time
    collector.record_job("aiEnrich", duration, success)
    collector.persist_if_due(60)
    stopWatch.end()
    footer(total, idx, totalCount, jobErrors, time.time() - _batch_start, duration)


def _save(repo: AiEnrichRepository, id, result: dict):
    validateResult(result)
    repo.update_enrichment(id, result.get("salary", None), result.get("required_technologies", None),
                           result.get("optional_technologies", None), result.get("modality", None))


def _handle_error(repo: AiEnrichRepository, id, title, company, ex, process_name):
    logger.exception("job.failed", job_id=id, title=title, company=company, error=str(ex))
    jobErrors.add((id, f"{title} - {company}: {ex}"))
    prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
    error_msg = f"{prefix}{ex}"
    if repo.update_enrichment_error(id, error_msg, True) == 0:
        logger.error("job.error_update_failed", job_id=id)
    else:
        logger.warning("job.error_set", job_id=id)


def _getJobIdsList(repo: AiEnrichRepository) -> list[int]:
    jobIds = repo.get_pending_enrichment_ids()
    logger.debug("job.pending_ids", ids=jobIds)
    return jobIds
