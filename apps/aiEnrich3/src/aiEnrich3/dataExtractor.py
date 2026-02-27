from typing import Optional, Tuple
from commonlib.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from aiEnrich3.pipeline import ExtractionPipeline
from aiEnrich3.config import get_batch_size, get_job_enabled
from aiEnrich3.services.job_enrichment_service import enrich_jobs, retry_failed_job
from commonlib.terminalColor import yellow


def dataExtractor(
    pipeline: Optional[ExtractionPipeline] = None,
) -> Tuple[int, Optional[ExtractionPipeline]]:
    if not get_job_enabled():
        return 0, None
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)

        # Check pending first to avoid loading models into RAM/VRAM if not needed
        total_pending = repo.count_pending_enrichment()
        error_id = repo.get_enrichment_error_id_retry()

        if total_pending == 0 and error_id is None:
            print("No jobs pending enrichment and no errors to retry.")
            # Unload pipeline if no jobs pending to save memory
            return 0, None

        if pipeline is None:
            print(
                yellow(
                    f"Loading Local CPU Pipeline (GLiNER & mDeBERTa) as there are {total_pending} jobs to process..."
                )
            )
            pipeline = ExtractionPipeline()

        processed = 0
        if error_id is not None:
            processed += retry_failed_job(repo, pipeline)

        if total_pending > 0:
            batch_size = get_batch_size()
            processed += enrich_jobs(repo, pipeline, batch_size)

        return processed, pipeline
