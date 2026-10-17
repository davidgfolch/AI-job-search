from .dataExtractor import dataExtractor, retry_failed_jobs
from commonlib.terminalColor import yellow, cyan
from commonlib.ai_helpers import logIdleWait
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

logger = get_logger("aiEnrich.pipeline")
collector = MetricsCollector()


def run_pipeline():
    while True:
        result = dataExtractor()
        if result == -1:
            logIdleWait(cyan('Backend unavailable, retrying... '), '10s', "ai.retry_wait", reason="backend_unavailable")
            continue
        if result == 0:
            retry_result = retry_failed_jobs()
            if retry_result == -1:
                logIdleWait(cyan('Backend unavailable, retrying... '), '10s', "ai.retry_wait", reason="backend_unavailable")
                continue
            if retry_result > 0:
                continue
        collector.persist()
        logIdleWait(cyan('All jobs enriched.'), '10s', "jobs.skipped", reason="no_pending_jobs")
