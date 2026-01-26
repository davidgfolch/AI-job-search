from crewai.flow.flow import Flow, start

from .cvMatcher import cvMatch
from commonlib.cv_loader import CVLoader
from commonlib.environmentUtil import getEnv
from .dataExtractor import dataExtractor
from .skillEnricher import skillEnricher
from commonlib.terminalColor import printHR, yellow, cyan
from commonlib.terminalUtil import consoleTimer
from commonlib.environmentUtil import getEnvBool

class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        cvLoader = CVLoader(cv_location=getEnv('CV_LOCATION', './cv/cv.txt'), enabled=getEnvBool('AI_CV_MATCH'))
        loadedCV = cvLoader.load_cv_content()
        while True:
            if dataExtractor()==0:
                if skillEnricher() > 0:
                    continue
                if getEnvBool('AI_CV_MATCH') and loadedCV:
                    if cvMatch() == 0:
                        consoleTimer(cyan('All jobs enriched & CV mached. '), '10s', end='\n')
                        continue
                continue
            printHR(yellow)
            consoleTimer(cyan('All jobs enriched. '), '10s', end='\n')
            

