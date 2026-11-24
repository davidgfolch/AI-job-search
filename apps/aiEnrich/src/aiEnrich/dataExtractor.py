import time
from typing import List

from commonlib.stopWatch import StopWatch
from commonlib.watcher_notify import notify_watcher as notify_backend_watcher
from commonlib.ai_helpers import (
    footer,
    mapJob,
    validateResult,
    RETRY_ERROR_PREFIX,
    logIdleWait,
    get_max_ai_input_chars,
    is_context_too_long,
)
from commonlib.terminalColor import cyan
from commonlib.repositories.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger, job_log_context
from commonlib.services.metrics_collector import MetricsCollector
from .aiEnrich_config import (
    get_model, get_max_validation_retries,
    get_backend, get_provider_model,
    get_max_ollama_failures, get_backend_url, get_timeout_job,
)
from .ollama_backend import (
    ping_backend, _query_job, _query_company,
    ollama_consecutive_failures,
)
from .extraction_contract import build_extraction_prompt, query_and_parse
from .companyExtractor import resolve_unspecified_company
from .technology_grounding import filter_ungrounded_technologies
from .hybrid_grounding import filter_ungrounded_hybrid_info

logger = get_logger("aiEnrich.dataExtractor")
collector = MetricsCollector()

DEBUG = False
stopWatch = StopWatch()
totalCount = 0
total = 0
jobErrors = set[tuple[int, str]]()
_batch_start = 0.0


def begin_batch() -> None:
    """Start the batch clock the footer reports against; the loops call it once per pass."""
    global _batch_start
    stopWatch.start()
    _batch_start = time.time()


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
    skipped = False
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
                model = get_provider_model(backend) if backend != "ollama" else get_model()
                logger.info("job.started", job_id=id, title=title, company=company, input_len=len(markdown), total=live_total, index=idx + 1, backend=backend, model=model, config=repo.config_for_job(id) or "NONE")
                prompt = build_extraction_prompt(title, markdown)
                result, response = None, None
                if is_context_too_long(prompt):
                    logger.warning("job.context_too_long", job_id=id, title=title, company=company, input_len=len(prompt), limit=get_max_ai_input_chars())
                    if repo.skip_enrichment(id) == 0:
                        logger.error("job.skip_update_failed", job_id=id)
                    skipped = True
                else:
                    while response is None:
                        if not ping_backend():
                            _wait_for_unavailable_backend(backend)
                            continue
                        result, response = query_and_parse(
                            lambda retry_prompt: _query_job(retry_prompt, backend, model), prompt,
                            max_attempts=get_max_validation_retries() + 1, log=logger,
                        )
                        if response is None and not ping_backend():
                            # The server died between the probe and the request: wait for it, the job stays pending.
                            _wait_for_unavailable_backend(backend)
                        elif response is None:
                            # The backend still answers the probe but produced no reply for this job (typically it does
                            # not finish within AI_ENRICH_TIMEOUT_JOB). Retrying it here re-ran the same request forever
                            # and blocked the whole batch, so the job leaves the pending queue with an error instead.
                            _mark_enrich_error(repo, id, title, company, f"no response from {backend} (timeout {get_timeout_job()}s)", process_name)
                            break
                    if result is not None:
                        filter_ungrounded_technologies(result, markdown, log=logger)
                        filter_ungrounded_hybrid_info(result, markdown, log=logger)
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
    if skipped:
        collector.record_job_skipped("aiEnrich")
    else:
        collector.record_job("aiEnrich", duration, success)
    collector.persist_if_due(60)
    stopWatch.end()
    footer(live_total, idx, totalCount, jobErrors, time.time() - _batch_start, duration, config=repo.config_for_job(id) or "NONE")


def _save(repo: AiEnrichRepository, id, result: dict):
    validateResult(result)
    repo.update_enrichment(id, result.get("salary", None), result.get("required_technologies", None),
                           result.get("optional_technologies", None), result.get("modality", None),
                           result.get("hybrid_info", None))
    _notify_watcher_backend([id])


def _notify_watcher_backend(job_ids: List[int]) -> None:
    """Tell the backend to enqueue enriched job IDs for watcher matching + SSE broadcast.

    Delegates to the shared client, which logs and swallows failures so enrichment
    keeps progressing after the job was already persisted.
    """
    if not job_ids:
        return
    notify_backend_watcher(job_ids, base_url=get_backend_url())


def _wait_for_unavailable_backend(backend: str) -> None:
    """An unreachable backend is waited for, never turned into a job error: the job stays pending."""
    logger.error("ai.unreachable", backend=backend, consecutive_failures=ollama_consecutive_failures, max_failures=get_max_ollama_failures())
    collector.record_backend_unreachable("aiEnrich")
    logIdleWait(cyan('Backend unavailable, retrying... '), '10s', "ai.retry_wait", reason="backend_unavailable")


def _mark_enrich_error(repo: AiEnrichRepository, id, title, company, reason: str, process_name: str):
    """Store a job-level error so the job leaves the pending queue instead of blocking the batch.

    Only used while the backend is up (its probe answers): a backend that is down is waited for by
    _wait_for_unavailable_backend. The retry pass picks the error up once and re-marks it with
    RETRY_ERROR_PREFIX if it fails again, which keeps a job that can never be enriched from looping.
    """
    logger.error("job.enrich_failed", job_id=id, title=title, company=company, reason=reason, config=repo.config_for_job(id) or "NONE")
    jobErrors.add((id, f"{title} - {company}: {reason}"))
    _persist_enrich_error(repo, id, reason, process_name)


def _persist_enrich_error(repo: AiEnrichRepository, id, error_msg, process_name: str):
    prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
    if repo.update_enrichment_error(id, f"{prefix}{error_msg}", True) == 0:
        logger.error("job.error_update_failed", job_id=id)
    else:
        logger.warning("job.error_set", job_id=id)


def _handle_error(repo: AiEnrichRepository, id, title, company, ex, process_name):
    logger.exception("job.failed", job_id=id, title=title, company=company, error=str(ex), config=repo.config_for_job(id) or "NONE")
    jobErrors.add((id, f"{title} - {company}: {ex}"))
    _persist_enrich_error(repo, id, ex, process_name)
