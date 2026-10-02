#!/usr/bin/env python
import sys
import warnings
from importlib.metadata import version as _v

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.observability import configure_logging, get_logger
from commonlib.ai_helpers import logIdleWait
from commonlib.terminalColor import cyan
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.services.metrics_collector import MetricsCollector
from .config import get_enabled, get_backend, get_ollama_base_url, get_max_ollama_failures
from .services.enrichment_service import enrich_skills
from commonlib.ollama_client import resolve_ollama_url

configure_logging("aiEnrichSkill")

logger = get_logger("aiEnrichSkill.main")
collector = MetricsCollector()


def run():
    logger.info("startup", version=_v('aiEnrichSkill'))

    if not get_enabled():
        logger.info("disabled")
        return

    ollama_consecutive_failures = 0
    while True:
        collector.record_heartbeat("aiEnrichSkill")
        ollama_base_url = get_ollama_base_url()
        if get_backend() == "ollama":
            ollama_base_url = resolve_ollama_url(primary_url=get_ollama_base_url(), log=logger)
            if ollama_base_url is None:
                ollama_consecutive_failures += 1
                max_failures = get_max_ollama_failures()
                logger.error("ollama.unreachable", base_url=get_ollama_base_url(), consecutive_failures=ollama_consecutive_failures, max_failures=max_failures)
                if ollama_consecutive_failures >= max_failures:
                    logger.critical("ollama.exit_threshold_reached", consecutive_failures=ollama_consecutive_failures)
                    sys.exit(1)
                logIdleWait(cyan('Ollama unreachable, retrying... '), '10s', "ai.retry_wait", reason="backend_unavailable")
                continue
            ollama_consecutive_failures = 0
        with MysqlUtil() as mysql:
            count = enrich_skills(mysql, ollama_base_url=ollama_base_url)
            if count > 0:
                collector.persist()
                continue
        collector.persist()
        logIdleWait(cyan('All skills enriched.'), '10s', "skill.enrich_skipped", reason="no_pending_skills")
