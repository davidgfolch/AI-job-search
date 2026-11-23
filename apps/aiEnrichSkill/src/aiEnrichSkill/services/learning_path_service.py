import time
from typing import List, Optional

from commonlib.ollama_activity import LOW_PRIORITY, request_slot
from commonlib.ollama_client import query_ollama
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

from ..config import get_learning_path_batch, get_ollama_base_url, get_ollama_model, get_timeout
from ..domain.mappers import build_learning_path_prompt_messages
from ..domain.parsers import parse_learning_path_result
from ..repositories.skill_repository import SkillRepository
from .idle_scheduler import LearningPathScheduler
from .link_validator import validate_learning_paths
from .skill_context_helper import fetch_skill_context_safe

logger = get_logger("aiEnrichSkill.learning_path_service")
collector = MetricsCollector()
MODULE = "aiEnrichSkillLearningPath"


class UnverifiableLearningPath(Exception):
    """One skill has no verifiable links: rotate it out instead of stalling the whole backfill."""


def generate_learning_path_ollama(skill_name: str, context: str = "", ollama_base_url: Optional[str] = None) -> List[str]:
    messages = build_learning_path_prompt_messages(skill_name, context)
    prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
    raw = query_ollama(
        prompt=prompt,
        model=get_ollama_model(),
        primary_url=ollama_base_url or get_ollama_base_url(),
        timeout=int(get_timeout()),
        json_mode=False,
        log=logger,
    )
    if raw is None:
        logger.error("skill.learning_path.failed", skill=skill_name)
        return []
    return parse_learning_path_result(raw)


def enrich_learning_paths(repository: SkillRepository, ollama_base_url: Optional[str] = None, scheduler: Optional[LearningPathScheduler] = None) -> int:
    """Low-priority backfill: starts only while the model is free and yields as soon as priority work appears."""
    scheduler = scheduler or LearningPathScheduler()
    batch = get_learning_path_batch()
    names = repository.fetch_pending_learning_path_names(max(batch * 5, 10))
    candidates = [name for name in names if not scheduler.should_skip(name)]
    if not candidates:
        scheduler.note_stopped()
        return 0
    updated = 0
    for name in candidates:
        if updated >= batch:
            break
        if repository.has_pending_enrichment():
            logger.info("skill.learning_path.yielded", skill=name, reason="priority_work")
            scheduler.note_stopped()
            break
        start = time.time()
        try:
            with request_slot(priority=LOW_PRIORITY) as acquired:
                if not acquired:
                    scheduler.note_deferred("model_busy")
                    return updated
                scheduler.note_started()
                urls = generate_learning_path_ollama(name, fetch_skill_context_safe(repository, name), ollama_base_url)
            learning_path = validate_learning_paths(name, urls)
            if not learning_path:
                raise UnverifiableLearningPath()
            repository.save_learning_path(name, learning_path)
            duration = time.time() - start
            collector.record_job(MODULE, duration, True)
            logger.info("skill.learning_path.saved", skill=name, links=len(learning_path), duration=duration)
            scheduler.note_success()
            updated += 1
        except UnverifiableLearningPath:
            duration = time.time() - start
            collector.record_job(MODULE, duration, False)
            collector.record_error(MODULE, "no verified learning path links")
            logger.info("skill.learning_path.skipped", skill=name, reason="no_verified_links", retry_after_seconds=scheduler.retry_seconds)
            scheduler.note_failed_skill(name)
        except Exception as exc:
            duration = time.time() - start
            collector.record_job(MODULE, duration, False)
            collector.record_error(MODULE, str(exc))
            logger.exception("skill.learning_path.failed", skill=name, error=str(exc))
            scheduler.note_failure()
            break
    return updated
