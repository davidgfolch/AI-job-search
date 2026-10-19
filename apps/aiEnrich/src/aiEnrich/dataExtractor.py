import time

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.ai_helpers import (
    footer,
    mapJob,
    validateResult,
    RETRY_ERROR_PREFIX,
    MAX_AI_ENRICH_ERROR_LEN,
    logIdleWait,
)
from commonlib.terminalColor import cyan
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger, job_log_context
from commonlib.services.metrics_collector import MetricsCollector
from .aiEnrich_config import (
    get_job_enabled, get_timeout_job, get_model, get_max_validation_retries,
    get_backend, get_ollama_base_url, get_openrouter_base_url, get_openrouter_model,
    get_openrouter_fallback_model, get_max_ollama_failures,
)
from .ollama_backend import (
    ping_backend, _check_backend_available, _query_job, _query_company,
    _resolved_ollama_url, _ollama_server_known, ollama_consecutive_failures,
)
from .extraction_contract import build_extraction_prompt, query_and_parse
from .openrouter_client import query_openrouter, ping_openrouter
from .companyExtractor import resolve_unspecified_company

logger = get_logger("aiEnrich.dataExtractor")
collector = MetricsCollector()

DEBUG = False
stopWatch = StopWatch()
totalCount = 0
total = 0
jobErrors = set[tuple[int, str]]()
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
        idx = 0
        for batch in _getJobBatches(repo):
            for id in batch:
                _process_job_safe(repo, id, total, idx, "enrich")
                idx += 1
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
    _remaining_pending = repo.count_pending_enrichment()
    live_total = max(total, idx + _remaining_pending, idx + 1)
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
                logger.info("job.started", job_id=id, title=title, company=company, input_len=len(markdown), total=live_total, index=idx + 1, backend=backend, model=model, config=repo.config_for_job(id) or "NONE")
                prompt = build_extraction_prompt(title, markdown)
                result, response = None, None
                while response is None:
                    if not ping_backend():
                        logger.error("ai.unreachable", backend=backend, consecutive_failures=ollama_consecutive_failures, max_failures=get_max_ollama_failures())
                        logIdleWait(cyan('Backend unavailable, retrying... '), '10s', "ai.retry_wait", reason="backend_unavailable")
                        continue
                    result, response = query_and_parse(
                        lambda retry_prompt: _query_job(retry_prompt, backend, model), prompt,
                        max_attempts=get_max_validation_retries() + 1, log=logger,
                    )
                    if response is None:
                        logger.warning("job.ai_unreachable", job_id=id, title=title, company=company)
                if result is not None:
                    _save(repo, id, result)
                    success = True
                    resolve_unspecified_company(repo, id, title, company, markdown, lambda p: _query_company(p, backend, model), log=logger)
                logger.info(
                    "job.result", job_id=id, result=result, duration=round(time.time() - start_time, 3), backend=backend,
                    model=model, done_reason=getattr(response, "done_reason", None),
                )
            except Exception as ex:
                _handle_error(repo, id, title, company, ex, process_name)
    except Exception as e:
        logger.error("job.critical_error", job_id=id, error=str(e))
    totalCount += 1
    duration = time.time() - start_time
    collector.record_job("aiEnrich", duration, success)
    collector.persist_if_due(60)
    stopWatch.end()
    footer(live_total, idx, totalCount, jobErrors, time.time() - _batch_start, duration, config=repo.config_for_job(id) or "NONE")


def _save(repo: AiEnrichRepository, id, result: dict):
    validateResult(result)
    repo.update_enrichment(id, result.get("salary", None), result.get("required_technologies", None),
                           result.get("optional_technologies", None), result.get("modality", None))


def _handle_error(repo: AiEnrichRepository, id, title, company, ex, process_name):
    logger.exception("job.failed", job_id=id, title=title, company=company, error=str(ex), config=repo.config_for_job(id) or "NONE")
    jobErrors.add((id, f"{title} - {company}: {ex}"))
    prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
    error_msg = f"{prefix}{ex}"
    if repo.update_enrichment_error(id, error_msg, True) == 0:
        logger.error("job.error_update_failed", job_id=id)
    else:
        logger.warning("job.error_set", job_id=id)


def _getJobBatches(repo: AiEnrichRepository):
    return repo.iter_pending_enrichment_batches()
