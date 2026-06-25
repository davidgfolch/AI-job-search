from .dataExtractor import dataExtractor, retry_failed_jobs
from commonlib.terminalColor import yellow, cyan
from commonlib.terminalUtil import consoleTimer
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

logger = get_logger("aiEnrich.pipeline")
collector = MetricsCollector()


def run_pipeline():
    while True:
        if dataExtractor() == 0:
            if retry_failed_jobs() > 0:
                continue
        collector.persist()
        consoleTimer(cyan('All jobs enriched. '), '10s', end='\n')
