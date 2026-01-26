from crewai.flow.flow import Flow, start

from .cvMatcher import cvMatch
from commonlib.cv_loader import CVLoader
from commonlib.environmentUtil import getEnv
from .dataExtractor import dataExtractor, retry_failed_jobs
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
                    if cvMatch() > 0:
                        continue
                
                # If all regular jobs and enriching are done, try retrying ONE failed job
                if retry_failed_jobs() > 0:
                    continue

            printHR(yellow)
            consoleTimer(cyan('All jobs enriched. '), '10s', end='\n')
            

