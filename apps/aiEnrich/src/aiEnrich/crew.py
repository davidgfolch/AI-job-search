from crewai.flow.flow import Flow, start

from .cvMatcher import cvMatch, loadCVContent
from .dataExtractor import dataExtractor
from commonlib.terminalColor import printHR, yellow
from commonlib.terminalUtil import consoleTimer
from commonlib.environmentUtil import getEnvBool

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
            

