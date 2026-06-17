#!/usr/bin/env python
import sys
import warnings
from importlib.metadata import version as _v

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.observability import configure_logging, get_logger
from commonlib.terminalColor import cyan
from commonlib.services.metrics_collector import MetricsCollector

configure_logging("aiEnrichNew")
from commonlib.terminalUtil import consoleTimer
import time
from .dataExtractor import dataExtractor, retry_failed_jobs
from .skillEnricher import skillEnricher
from .config import get_job_enabled, get_skill_enabled

logger = get_logger("aiEnrichNew.main")
collector = MetricsCollector()

def run():
    logger.info("startup", version=_v('aiEnrichNew'))
    print(cyan(f"AI Enrich New v{_v('aiEnrichNew')}"))

    while True:
        if get_job_enabled() and dataExtractor() > 0:
            collector.persist()
            continue
        if get_skill_enabled() and skillEnricher() > 0:
            continue
        if retry_failed_jobs() > 0:
            collector.persist()
            continue
        consoleTimer(cyan('All jobs enriched. '), '10s', end='\r')
