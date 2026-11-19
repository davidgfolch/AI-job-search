import time

from commonlib.observability import get_logger
from commonlib.skill_learning_path import LearningPathLink
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.services.skill_enricher_service import BackendUnavailable, process_skill_enrichment

from ..config import get_backend, get_ollama_model, get_ollama_base_url, get_timeout, get_enrich_limit
from ..repositories.skill_repository import SkillRepository
from commonlib.ollama_client import ping_ollama, query_ollama
from ..domain.mappers import build_skill_prompt_messages
from ..domain.parsers import parse_skill_enrichment_result
from .hf_enrichment import _enrich_huggingface
from .link_validator import validate_learning_paths

logger = get_logger("aiEnrichSkill.enrichment")
collector = MetricsCollector()


def generate_skill_description_ollama(skill_name, context="", ollama_base_url=None) -> tuple[str, str, list[LearningPathLink]]:
    logger.info("skill.started", skill=skill_name, has_context=bool(context))
    messages = build_skill_prompt_messages(skill_name, context)
    system = messages[0]["content"]
    user = messages[1]["content"]
    prompt = f"{system}\n\n{user}"

    raw = query_ollama(
        prompt=prompt,
        model=get_ollama_model(),
        primary_url=ollama_base_url or get_ollama_base_url(),
        timeout=int(get_timeout()),
        json_mode=False,
        log=logger,
    )
    if raw is None:
        logger.error("skill.failed", skill=skill_name)
        return ("", "Other", [])

    result = raw.strip().strip('"').strip("'")
    parsed = parse_skill_enrichment_result(result)
    description, category, *rest = parsed
    learning_path = validate_learning_paths(skill_name, rest[0] if rest else [])
    logger.info("skill.completed", skill=skill_name, has_description=bool(description), links=len(learning_path))
    return description, category, learning_path


def _backend_is_up(ollama_base_url=None) -> bool:
    """Liveness ping: the only signal that separates "the server is gone" from "it cannot do this skill"."""
    return ping_ollama(primary_url=ollama_base_url or get_ollama_base_url(), log=logger)


def _handle_failed_skill(repository: SkillRepository, name: str, ollama_base_url=None) -> None:
    """Ollama up: the skill leaves the pending queue, or retrying it every cycle would keep the head of
    the queue occupied forever. Ollama down: nothing is marked, the batch stops (BackendUnavailable)
    and the worker retries the skill once the server answers again."""
    if not _backend_is_up(ollama_base_url):
        logger.error("ai.unreachable", backend="ollama", skill=name)
        raise BackendUnavailable(name)
    repository.skip_skill(name)
    logger.error("skill.enrich_error", skill=name, reason="no description from the model")


def _enrich_ollama(repository: SkillRepository, ollama_base_url=None) -> int:
    if repository.has_pending_enrichment() and not _backend_is_up(ollama_base_url):
        # Deferred, never marked: the pending skills are retried when Ollama is back.
        logger.error("ai.unreachable", backend="ollama", base_url=ollama_base_url or get_ollama_base_url())
        collector.record_backend_unreachable("aiEnrichSkill")
        return 0

    def timed_generate(name, context):
        start = time.time()
        try:
            result = generate_skill_description_ollama(name, context, ollama_base_url)
        except Exception as e:
            collector.record_job("aiEnrichSkill", time.time() - start, False)
            collector.record_error("aiEnrichSkill", str(e))
            _handle_failed_skill(repository, name, ollama_base_url)
            return ("", "Other", [])
        duration = time.time() - start
        description = result[0] if isinstance(result, tuple) and len(result) >= 2 else (result if isinstance(result, str) else "")
        success = bool(description) and "Error" not in description
        collector.record_job("aiEnrichSkill", duration, success)
        logger.info("skill.result", duration=duration, skill=name, success=success)
        if not success:
            _handle_failed_skill(repository, name, ollama_base_url)
        return result
    return process_skill_enrichment(
        repository,
        timed_generate,
        limit=get_enrich_limit(),
        check_empty_description_only=True,
    )


def enrich_skills(repository: SkillRepository, ollama_base_url=None) -> int:
    backend = get_backend()
    if backend == "ollama":
        return _enrich_ollama(repository, ollama_base_url)
    elif backend == "huggingface":
        return _enrich_huggingface(repository)
    else:
        logger.error("unknown_backend", backend=backend)
        return 0
