#!/usr/bin/env python
import sys
import warnings

# Validated lazy imports

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.util import getEnvBool
from commonlib.terminalColor import yellow, printHR
from commonlib.util import consoleTimer
import time
from .dataExtractor import dataExtractor
from .fastCvMatcher import FastCVMatcher

def run():
    if getEnvBool('AI_CV_MATCH'):
        cvMatcher = FastCVMatcher.instance()
    else:
        cvMatcher = None

    while True:
        if dataExtractor()==0:
            if cvMatcher is not None:
                cvMatcher.process_db_jobs()
                consoleTimer('All jobs enriched & CV matched. ', '10s', end='\n')
                continue
        printHR(yellow)
        consoleTimer('All jobs enriched. ', '10s', end='\n')