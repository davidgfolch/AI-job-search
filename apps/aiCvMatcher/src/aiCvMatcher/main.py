#!/usr/bin/env python
import sys
import warnings

# Validated lazy imports
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.environmentUtil import getEnvBool
from commonlib.terminalColor import yellow, printHR, cyan
from commonlib.terminalUtil import consoleTimer
import time
from .cvMatcher import FastCVMatcher

def run():
    if getEnvBool('AI_CVMATCHER_ENABLED'):
        cvMatcher = FastCVMatcher.instance()
    else:
        print(yellow("AI_CVMATCHER_ENABLED is not enabled. Exiting CV Matcher loop."))
        sys.exit(0)

    while True:
        if cvMatcher.process_db_jobs() > 0:
            continue
        consoleTimer(cyan('All CV matches calculated. '), '10s', end='\r')

if __name__ == "__main__":
    run()
