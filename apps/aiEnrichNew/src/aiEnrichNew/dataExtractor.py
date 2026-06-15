from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector
from .llm_client import get_pipeline
from .config import get_batch_size, get_job_enabled
from .services.job_enrichment_service import enrich_jobs, retry_failed_job

logger = get_logger("aiEnrichNew.dataExtractor")
collector = MetricsCollector()

def dataExtractor() -> int:
    if not get_job_enabled():
        return 0
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        total = repo.count_pending_enrichment()
        if total == 0:
            return 0
        logger.info("jobs.found", total=total, module="aiEnrichNew")
        collector.set_pending("aiEnrichNew", total)
        pipe = get_pipeline()
        return enrich_jobs(repo, pipe, get_batch_size())

def retry_failed_jobs() -> int:
    if not get_job_enabled():
        return 0
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        pipe = get_pipeline()
        return retry_failed_job(repo, pipe)
