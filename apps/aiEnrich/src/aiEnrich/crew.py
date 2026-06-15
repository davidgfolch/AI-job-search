from crewai.flow.flow import Flow, start

from .dataExtractor import dataExtractor, retry_failed_jobs
from .skillEnricher import skillEnricher
from commonlib.terminalColor import printHR, yellow, cyan
from commonlib.terminalUtil import consoleTimer
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

logger = get_logger("aiEnrich.crew")
collector = MetricsCollector()

class AiJobSearchFlow(Flow):
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        while True:
            if dataExtractor()==0:
                if skillEnricher() > 0:
                    continue
                if retry_failed_jobs() > 0:
                    continue
            collector.persist()
            printHR(yellow)
            consoleTimer(cyan('All jobs enriched. '), '10s', end='\n')
            

