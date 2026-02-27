from commonlib.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from .llm_client import get_pipeline
from .config import get_batch_size, get_job_enabled
from .services.job_enrichment_service import enrich_jobs, retry_failed_job

def dataExtractor() -> int:
    if not get_job_enabled():
        return 0
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        # Check pending first to avoid loading pipeline if not needed
        # Although enrich_jobs does this too, we might want to avoid get_pipeline overhead
        # But get_pipeline is lazy in llm_client globally? No, it's global variable but init on call.
        # But enrich_jobs logic:
        # total = repo.count_pending_enrichment()
        # if total == 0: return 0
        # Pipeline is only used if total > 0.
        
        # However, we need to pass pipeline.
        # So we can pass a lambda or just get it. 
        # get_pipeline() is fast if already loaded. If not loaded, it loads.
        # We don't want to load it if there are no jobs.
        
        total = repo.count_pending_enrichment()
        if total == 0:
            return 0
            
        pipe = get_pipeline()
        return enrich_jobs(repo, pipe, get_batch_size())

def retry_failed_jobs() -> int:
    if not get_job_enabled():
        return 0
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        pipe = get_pipeline()
        return retry_failed_job(repo, pipe)
