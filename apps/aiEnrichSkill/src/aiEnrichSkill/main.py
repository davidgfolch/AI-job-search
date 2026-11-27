#!/usr/bin/env python
import warnings
from importlib.metadata import version as _v

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.observability import configure_logging, get_logger
from commonlib.ai_helpers import logIdleWait, idleWait
from commonlib.terminalColor import cyan
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.sql.connection_manager import wait_for_db
from commonlib.services.metrics_collector import MetricsCollector
from .config import get_enabled, get_backend, get_ollama_base_url, get_max_ollama_failures
from .repositories.skill_repository import SkillRepository
from .services.enrichment_service import enrich_skills
from .services.idle_scheduler import LearningPathScheduler, should_run_learning_paths
from .services.learning_path_service import enrich_learning_paths
from commonlib.ollama_client import resolve_ollama_url

configure_logging("aiEnrichSkill")

logger = get_logger("aiEnrichSkill.main")
collector = MetricsCollector()


def _resolve_ollama_url() -> str:
    """Resolve Ollama with the same bounded wait the worker uses at startup."""
    ollama_consecutive_failures = 0
    while True:
        resolved_url = resolve_ollama_url(primary_url=get_ollama_base_url(), log=logger)
        if resolved_url is not None:
            return resolved_url
        ollama_consecutive_failures += 1
        max_failures = get_max_ollama_failures()
        logger.error("ollama.unreachable", base_url=get_ollama_base_url(), consecutive_failures=ollama_consecutive_failures, max_failures=max_failures)
        if ollama_consecutive_failures == max_failures:
            # Keep waiting: exiting here turned a sleeping Ollama server into a
            # container restart storm that starved the database on resume.
            logger.critical("ollama.waiting_after_failures", consecutive_failures=ollama_consecutive_failures)
        logIdleWait(cyan('Ollama unreachable, retrying... '), '10s', "ai.retry_wait", reason="backend_unavailable")


def run():
    logger.info("startup", version=_v('aiEnrichSkill'))

    if not get_enabled():
        logger.info("disabled")
        return

    wait_for_db(log=logger)
    active_backend = get_backend()
    ollama_base_url = _resolve_ollama_url() if active_backend == "ollama" else get_ollama_base_url()

    scheduler = LearningPathScheduler()
    while True:
        backend = get_backend()
        if backend != active_backend:
            active_backend = backend
            if backend == "ollama":
                # A live switch back from HuggingFace needs a fresh URL in this process.
                ollama_base_url = _resolve_ollama_url()
        collector.record_heartbeat("aiEnrichSkill")
        with MysqlUtil() as mysql:
            repository = SkillRepository(mysql)
            count = enrich_skills(repository, ollama_base_url=ollama_base_url)
            if count > 0:
                collector.persist()
                continue
            if should_run_learning_paths(scheduler):
                paths = enrich_learning_paths(repository, ollama_base_url=ollama_base_url, scheduler=scheduler)
                if paths > 0:
                    collector.persist()
                    continue
            else:
                scheduler.note_stopped()
        collector.persist()
        if scheduler.deferred:
            # The backfill already recorded `skill.learning_path.deferred` for this cycle.
            idleWait(cyan('Ollama busy, waiting for a free slot.'), '3s')
        else:
            idleWait(cyan('All skills enriched.'), '10s')
