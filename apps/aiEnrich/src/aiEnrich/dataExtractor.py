import sys
import time
import traceback

from commonlib.json_helpers import rawToJson
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.ai_helpers import (
    footer,
    mapJob,
    printJob,
    validateResult,
    RETRY_ERROR_PREFIX,
    MAX_AI_ENRICH_ERROR_LEN,
)
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger
from commonlib.aiEnrich_config import (
    get_job_enabled, get_ollama_base_url, get_timeout_job, get_model, get_max_ollama_failures,
    get_backend, get_openrouter_base_url, get_openrouter_model, get_openrouter_fallback_model,
)
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.ollama_client import query_ollama, resolve_ollama_url
from .openrouter_client import query_openrouter, ping_openrouter

logger = get_logger("aiEnrich.dataExtractor")
collector = MetricsCollector()

PROMPT_TEMPLATE = """Analyze the following job offer and extract structured information.

Job Offer:
{markdown}

Extract the following information:
- Required technologies (comma-separated list)
- Optional technologies (comma-separated list)
- Salary information (if available)
- Modality (must be exactly REMOTE, HYBRID, or ON_SITE)

A valid JSON object with the extracted information. Include all fields even if empty.
IMPORTANT: Use JSON ARRAYS for technology lists (e.g., ["technology1", "technology2"]). Do NOT use comma-separated strings inside quotes.
The json output must have the following fields and structure:
{{
  "required_technologies": ["technology1", "technology2"],
  "optional_technologies": ["technology3", "technology4"],
  "salary": "...",
  "modality": "..."
}}"""


_resolved_ollama_url: str | None = None


def _get_ollama_base_url() -> str:
    return _resolved_ollama_url or get_ollama_base_url()


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
    logger.error("ai.unreachable", backend=get_backend(), module="aiEnrich", consecutive_failures=ollama_consecutive_failures, max_failures=max_failures)
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


def dataExtractor() -> int:
    global totalCount, jobErrors
    if not get_job_enabled():
        return 0
    if not _check_backend_available():
        return -1
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        total = repo.count_pending_enrichment()
        if total is None or total == 0:
            return 0
        logger.info("jobs.found", total=total, module="aiEnrich")
        collector.set_pending("aiEnrich", total)
        stopWatch.start()
        for idx, id in enumerate(_getJobIdsList(repo)):
            _process_job_safe(repo, id, total, idx, "enrich")
        return total


def retry_failed_jobs() -> int:
    global totalCount, jobErrors
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
        job = repo.get_job_to_enrich(id) if process_name == "enrich" else repo.get_job_to_retry(id)
        if job is None:
            logger.warning("job.not_found", job_id=id)
            return
        title, company, markdown = mapJob(job)
        try:
            backend = get_backend()
            model = get_openrouter_model() if backend == "openrouter" else get_model()
            logger.info("job.started", job_id=id, title=title, company=company, input_len=len(markdown), total=total, index=idx, backend=backend, model=model)
            prompt = PROMPT_TEMPLATE.format(markdown=f"# {title} \n {markdown}")
            if get_backend() == "openrouter":
                raw = query_openrouter(
                    prompt=prompt,
                    model=get_openrouter_model(),
                    base_url=get_openrouter_base_url(),
                    timeout=get_timeout_job(),
                    json_mode=False,
                    fallback_model=get_openrouter_fallback_model(),
                )
            else:
                raw = query_ollama(
                    prompt=prompt,
                    model=get_model(),
                    primary_url=_get_ollama_base_url(),
                    timeout=get_timeout_job(),
                    json_mode=True,
                    log=logger,
                )
            if raw is None:
                logger.warning("job.skipped_ai_unreachable", job_id=id, title=title, company=company)
            else:
                result = rawToJson(raw)
                if result is not None:
                    _save(repo, id, result)
                    success = True
                logger.info("job.result", job_id=id, result=result, duration=round(time.time() - start_time, 3), backend=backend, model=model)
        except (Exception, KeyboardInterrupt) as ex:
            _handle_error(repo, id, title, company, ex, process_name)
    except Exception as e:
        logger.error("job.critical_error", job_id=id, error=str(e))
    totalCount += 1
    duration = time.time() - start_time
    collector.record_job("aiEnrich", duration, success)
    collector.persist_if_due(60)
    stopWatch.end()
    footer(total, idx, totalCount, jobErrors)


def _save(repo: AiEnrichRepository, id, result: dict):
    validateResult(result)
    repo.update_enrichment(id, result.get("salary", None), result.get("required_technologies", None),
                           result.get("optional_technologies", None), result.get("modality", None))


def _handle_error(repo: AiEnrichRepository, id, title, company, ex, process_name):
    logger.error("job.failed", job_id=id, title=title, company=company, error=str(ex), traceback=traceback.format_exc())
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
