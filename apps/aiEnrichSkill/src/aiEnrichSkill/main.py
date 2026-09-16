#!/usr/bin/env python
import sys
import time
import warnings
from importlib.metadata import version as _v

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.observability import configure_logging, get_logger
from commonlib.terminalColor import cyan
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.terminalUtil import consoleTimer
from commonlib.services.metrics_collector import MetricsCollector
from .config import get_enabled, get_backend, get_ollama_base_url, get_max_ollama_failures
from .services.enrichment_service import enrich_skills
from .ollama_client import ping_ollama

configure_logging("aiEnrichSkill")

logger = get_logger("aiEnrichSkill.main")
collector = MetricsCollector()


def run():
    logger.info("startup", version=_v('aiEnrichSkill'))
    print(cyan(f"AI Skill Enrich v{_v('aiEnrichSkill')}"))

    if not get_enabled():
        logger.info("disabled")
        return

    ollama_consecutive_failures = 0
    while True:
        collector.record_heartbeat("aiEnrichSkill")
        if get_backend() == "ollama" and not ping_ollama(base_url=get_ollama_base_url()):
            ollama_consecutive_failures += 1
            max_failures = get_max_ollama_failures()
            logger.error("ollama.unreachable", base_url=get_ollama_base_url(), consecutive_failures=ollama_consecutive_failures, max_failures=max_failures)
            if ollama_consecutive_failures >= max_failures:
                logger.critical("ollama.exit_threshold_reached", consecutive_failures=ollama_consecutive_failures)
                sys.exit(1)
            consoleTimer(cyan('Ollama unreachable, retrying... '), '10s', end='\r')
            continue
        ollama_consecutive_failures = 0
        with MysqlUtil() as mysql:
            count = enrich_skills(mysql)
            if count > 0:
                collector.persist()
                continue
        collector.persist()
        consoleTimer(cyan('All skills enriched. '), '10s', end='\r')
