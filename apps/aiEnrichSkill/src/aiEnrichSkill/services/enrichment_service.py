import time

from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

from ..config import get_backend, get_ollama_model, get_ollama_base_url, get_timeout, get_enrich_limit
from ..repositories.skill_repository import SkillRepository
from commonlib.ollama_client import query_ollama
from ..domain.mappers import build_skill_prompt_messages
from ..domain.parsers import parse_skill_enrichment_result
from .hf_enrichment import _enrich_huggingface
from .link_validator import validate_learning_paths

logger = get_logger("aiEnrichSkill.enrichment")
collector = MetricsCollector()


def generate_skill_description_ollama(skill_name, context="", ollama_base_url=None) -> tuple[str, str, list[str]]:
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


def _enrich_ollama(repository: SkillRepository, ollama_base_url=None) -> int:
    def timed_generate(name, context):
        start = time.time()
        try:
            result = generate_skill_description_ollama(name, context, ollama_base_url)
            duration = time.time() - start
            description = result[0] if isinstance(result, tuple) and len(result) >= 2 else (result if isinstance(result, str) else "")
            success = bool(description) and "Error" not in description
            collector.record_job("aiEnrichSkill", duration, success)
            logger.info("skill.result", duration=duration, skill=name, success=success)
            return result
        except Exception as e:
            duration = time.time() - start
            collector.record_job("aiEnrichSkill", duration, False)
            collector.record_error("aiEnrichSkill", str(e))
            return ("", "Other", [])
    return repository.run_pending_enrichment(
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
