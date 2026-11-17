import time
from typing import Any, Dict, List

from commonlib.skill_enricher_service import log_no_pending_skills
from commonlib.stopWatch import StopWatch
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

from ..config import get_batch_size, get_enrich_limit, get_timeout
from ..domain.mappers import build_skill_prompt_messages
from ..domain.parsers import parse_skill_enrichment_result
from ..repositories.skill_repository import SkillRepository
from .link_validator import validate_learning_paths
from .skill_context_helper import fetch_skill_context_safe

logger = get_logger("aiEnrichSkill.hf_enrichment")
collector = MetricsCollector()


def _enrich_huggingface(repository: SkillRepository) -> int:
    from ..llm_client import get_pipeline

    batch_size = get_batch_size()
    limit = get_enrich_limit()

    skills = [{'name': name} for name in repository.fetch_pending_skill_names(limit)]
    if not skills:
        log_no_pending_skills(limit)
        return 0

    collector.set_pending("aiEnrichSkill", len(skills))
    logger.info("skills.found", total=len(skills), batch_size=batch_size)

    pipe = get_pipeline()
    count = 0
    overall_start_time = time.time()

    for i in range(0, len(skills), batch_size):
        batch_items = skills[i:i + batch_size]
        processed_count = _process_skill_batch(
            repository, pipe, batch_items, i, len(skills), count, overall_start_time
        )
        count += processed_count

    print("-" * 50)
    return count


def _process_skill_batch(
    repository: SkillRepository,
    pipeline: Any,
    batch_items: List[Dict[str, str]],
    start_idx: int,
    total: int,
    _current_global_count: int,
    _start_time: float
) -> int:
    from ..llm_utils import process_batch

    stop_watch_batch = StopWatch()
    stop_watch_batch.start()

    success_count = 0

    def apply_template(tokenizer, messages):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def build_messages_with_context(item: Dict[str, str]) -> List[dict]:
        name = item['name']
        idx = batch_items.index(item)
        current_idx = start_idx + idx + 1
        context = fetch_skill_context_safe(repository, name)
        logger.info("skill.started", skill=name, index=current_idx, total=total)
        return build_skill_prompt_messages(name, context)

    _timing = {"last": time.time()}

    def on_success(item: Dict[str, str], generated_text: str):
        nonlocal success_count
        name = item['name']
        now = time.time()
        duration = now - _timing["last"]
        _timing["last"] = now
        description, category, *rest = parse_skill_enrichment_result(generated_text)
        learning_path = validate_learning_paths(name, rest[0] if rest else [])
        success = bool(description) and "Error" not in description
        collector.record_job("aiEnrichSkill", duration, success)
        logger.info("skill.result", duration=duration, skill=name, success=success)
        if success:
            repository.save_skill_result(name, description, category, learning_path)
            success_count += 1
        else:
            logger.warning("skill.failed_to_generate", skill=name)

    def on_error(item: Dict[str, str], ex: Exception):
        name = item['name']
        now = time.time()
        duration = now - _timing["last"]
        _timing["last"] = now
        collector.record_job("aiEnrichSkill", duration, False)
        collector.record_error("aiEnrichSkill", str(ex))
        logger.info("skill.result", duration=duration, skill=name, success=False)
        logger.exception("skill.failed", skill=name, error=str(ex))

    process_batch(
        pipeline,
        batch_items,
        apply_template,
        build_messages_with_context,
        on_success,
        on_error,
        get_timeout(),
        "skills"
    )

    stop_watch_batch.end()
    return success_count
