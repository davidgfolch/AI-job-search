from crewai.flow.flow import Flow, start

from .dataExtractor import dataExtractor, retry_failed_jobs
from .skillEnricher import skillEnricher
from commonlib.terminalColor import printHR, yellow, cyan
from commonlib.terminalUtil import consoleTimer

class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        while True:
            if dataExtractor()==0:
                if skillEnricher() > 0:
                    continue
                # If all regular jobs and enriching are done, try retrying ONE failed job
                if retry_failed_jobs() > 0:
                    continue
            printHR(yellow)
            consoleTimer(cyan('All jobs enriched. '), '10s', end='\n')
            

