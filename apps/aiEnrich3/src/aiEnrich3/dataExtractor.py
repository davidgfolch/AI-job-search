import time
from typing import Optional, Tuple
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector
from aiEnrich3.pipeline import ExtractionPipeline
from aiEnrich3.config import get_batch_size, get_job_enabled
from aiEnrich3.services.job_enrichment_service import enrich_jobs, retry_failed_job

logger = get_logger("aiEnrich3.dataExtractor")
collector = MetricsCollector()


def dataExtractor(
    pipeline: Optional[ExtractionPipeline] = None,
) -> Tuple[int, Optional[ExtractionPipeline]]:
    if not get_job_enabled():
        return 0, None
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        total_pending = repo.count_pending_enrichment()
        error_id = repo.get_enrichment_error_id_retry()

        if total_pending == 0 and error_id is None:
            return 0, None

        if pipeline is None:
            logger.info("pipeline.loading", total_pending=total_pending)
            pipeline = ExtractionPipeline()

        collector.set_pending("aiEnrich3", total_pending)

        processed = 0
        if error_id is not None:
            processed += retry_failed_job(repo, pipeline)

        if total_pending > 0:
            batch_size = get_batch_size()
            processed += enrich_jobs(repo, pipeline, batch_size)

        return processed, pipeline
