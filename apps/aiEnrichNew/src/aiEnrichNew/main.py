#!/usr/bin/env python
import sys
import warnings

# Validated lazy imports

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.environmentUtil import getEnvBool
from commonlib.terminalColor import yellow, printHR, cyan
from commonlib.terminalUtil import consoleTimer
import time
from .dataExtractor import dataExtractor, retry_failed_jobs
from .skillEnricher import skillEnricher

def run():

    while True:
        if dataExtractor() > 0:
            continue
        if skillEnricher() > 0:
            continue
        if retry_failed_jobs() > 0:
            continue
        consoleTimer(cyan('All jobs enriched. '), '10s', end='\r')