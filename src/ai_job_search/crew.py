from crewai.flow.flow import Flow, start

from ai_job_search.crewai.cvMatcher import cvMatch, loadCVContent
from ai_job_search.crewai.dataExtractor import dataExtractor
from .tools.terminalColor import printHR, yellow
from .tools.util import consoleTimer, getEnvBool

class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        loadedCV = loadCVContent()
        while True:
            if dataExtractor()==0:
                if getEnvBool('AI_CV_MATCH') and loadedCV:
                    if cvMatch() == 0:
                        consoleTimer('All jobs enriched & CV mached. ', '10s', end='\n')
                        continue
                continue
            printHR(yellow)
            consoleTimer('All jobs enriched. ', '10s', end='\n')
            

