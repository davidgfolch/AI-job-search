"""Batch loops of the aiEnrich worker.

Split out of `dataExtractor` (which keeps the per-job processing): a loop picks the pending
(or failed) jobs and hands each one to `_process_job_safe`, skipping the jobs whose filter
configuration was re-applied and no longer matches them.
"""
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.repositories.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger
from .aiEnrich_config import get_job_enabled
from .ollama_backend import _check_backend_available
from .dataExtractor import begin_batch, collector, _process_job_safe

logger = get_logger("aiEnrich.enrichRunner")


def _recheck_filter_config(repo: AiEnrichRepository, selector, job_id: int) -> bool:
    """True when `job_id` must be skipped: the configuration that matched it was edited.

    A job with no original configuration, or with no configuration loaded at all, keeps its place
    in the pass; otherwise the current configuration names the job again or the job is dropped.
    """
    if not repo.config_for_job(job_id):
        return False
    configs = selector.load_configs()
    if not configs:
        return False
    matched_name = next((cfg["name"] for cfg in configs if selector.match_ids(cfg["filters"], limit=1, job_id=job_id)), None)
    if matched_name is None:
        return True
    repo._job_configs[job_id] = matched_name
    return False


def _getJobBatches(repo: AiEnrichRepository):
    return repo.iter_pending_enrichment_batches()


def dataExtractor() -> int:
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
        begin_batch()
        idx = 0
        from commonlib.sql.filter_config_selector import FilterConfigSelector
        selector = FilterConfigSelector(mysql)
        for batch in _getJobBatches(repo):
            for id in batch:
                try:
                    if _recheck_filter_config(repo, selector, id):
                        idx += 1
                        continue
                except Exception:
                    logger.exception("job.fc_recheck_failed", job_id=id)
                _process_job_safe(repo, id, total, idx, "enrich")
                idx += 1
        return total


def retry_failed_jobs() -> int:
    if not get_job_enabled():
        return 0
    if not _check_backend_available():
        return -1
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        error_id = repo.get_enrichment_error_id_retry()
        if error_id is None:
            return 0
        try:
            from commonlib.sql.filter_config_selector import FilterConfigSelector
            selector = FilterConfigSelector(mysql)
            if _recheck_filter_config(repo, selector, error_id):
                return 1
        except Exception:
            logger.exception("job.fc_recheck_failed", job_id=error_id)
        logger.info("job.retry", job_id=error_id)
        begin_batch()
        _process_job_safe(repo, error_id, 1, 0, "retry")
        return 1
