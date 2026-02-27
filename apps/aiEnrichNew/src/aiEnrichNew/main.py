#!/usr/bin/env python
import sys
import warnings

# Validated lazy imports

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.terminalColor import yellow, printHR, cyan
from commonlib.terminalUtil import consoleTimer
import time
from .dataExtractor import dataExtractor, retry_failed_jobs
from .skillEnricher import skillEnricher
from .config import get_job_enabled, get_skill_enabled

def run():

    while True:
        if get_job_enabled() and dataExtractor() > 0:
            continue
        if get_skill_enabled() and skillEnricher() > 0:
            continue
        if retry_failed_jobs() > 0:
            continue
        consoleTimer(cyan('All jobs enriched. '), '10s', end='\r')