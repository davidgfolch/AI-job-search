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
from .cvMatcher import FastCVMatcher

def run():
    if getEnvBool('AI_CV_MATCH'):
        cvMatcher = FastCVMatcher.instance()
    else:
        cvMatcher = None

    while True:
        if dataExtractor()==0:
            if cvMatcher is not None:
                if cvMatcher.process_db_jobs()>0:
                    continue
        printHR(yellow)
        consoleTimer('All jobs enriched. ', '10s', end='\n')