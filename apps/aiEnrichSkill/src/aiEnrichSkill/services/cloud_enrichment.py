import time

from commonlib.cloud_llm import chat, ping
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.services.skill_enricher_service import process_skill_enrichment

from ..config import get_backend, get_enrich_limit, get_provider_model, get_timeout
from ..domain.mappers import build_skill_prompt_messages
from ..domain.parsers import parse_skill_enrichment_result
from ..repositories.skill_repository import SkillRepository
from .link_validator import validate_learning_paths

logger = get_logger("aiEnrichSkill.cloud_enrichment")
collector = MetricsCollector()


def generate_skill_description_cloud(skill_name, context="") -> tuple[str, str, list]:
    provider = get_backend()
    logger.info("skill.started", skill=skill_name, provider=provider, has_context=bool(context))
    raw = chat(provider, messages=build_skill_prompt_messages(skill_name, context), timeout=int(get_timeout()), model=get_provider_model())
    if raw is None:
        logger.error("skill.failed", skill=skill_name, provider=provider)
        return ("", "Other", [])
    description, category, *rest = parse_skill_enrichment_result(raw.strip().strip('"').strip("'"))
    learning_path = validate_learning_paths(skill_name, rest[0] if rest else [])
    logger.info("skill.completed", skill=skill_name, has_description=bool(description), links=len(learning_path))
    return description, category, learning_path


def _enrich_cloud(repository: SkillRepository) -> int:
    provider = get_backend()
    if repository.has_pending_enrichment() and not ping(provider):
        logger.error("ai.unreachable", backend=provider)
        collector.record_backend_unreachable("aiEnrichSkill")
        return 0

    def timed_generate(name, context):
        start = time.time()
        try:
            result = generate_skill_description_cloud(name, context)
        except Exception as e:
            collector.record_job("aiEnrichSkill", time.time() - start, False)
            collector.record_error("aiEnrichSkill", str(e))
            repository.skip_skill(name)
            return ("", "Other", [])
        duration = time.time() - start
        success = bool(result[0]) and "Error" not in result[0]
        collector.record_job("aiEnrichSkill", duration, success)
        logger.info("skill.result", duration=duration, skill=name, success=success)
        if not success:
            repository.skip_skill(name)
        return result

    return process_skill_enrichment(
        repository, timed_generate, limit=get_enrich_limit(), check_empty_description_only=True,
    )
