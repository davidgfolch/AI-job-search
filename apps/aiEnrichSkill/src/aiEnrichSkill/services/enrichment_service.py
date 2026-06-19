import time
import json
import traceback
from typing import List, Dict, Any

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.skill_enricher_service import process_skill_enrichment
from commonlib.terminalColor import yellow, magenta, cyan, red, green
from commonlib.stopWatch import StopWatch
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.observability import get_logger

from ..config import get_backend, get_ollama_model, get_ollama_base_url, get_timeout, get_batch_size, get_enrich_limit, get_gpu_cleanup
from ..ollama_client import query_ollama
from ..domain.mappers import build_skill_prompt_messages
from ..domain.parsers import parse_skill_enrichment_result

logger = get_logger("aiEnrichSkill.enrichment")


def generate_skill_description_ollama(skill_name, context="") -> tuple[str, str]:
    logger.info("skill.started", skill=skill_name, has_context=bool(context))
    messages = build_skill_prompt_messages(skill_name, context)
    system = messages[0]["content"]
    user = messages[1]["content"]
    prompt = f"{system}\n\n{user}"

    raw = query_ollama(
        prompt=prompt,
        model=get_ollama_model(),
        base_url=get_ollama_base_url(),
        timeout=int(get_timeout()),
        json_mode=False,
    )
    if raw is None:
        logger.error("skill.failed", skill=skill_name)
        return ("", "Other")

    result = raw.strip().strip('"').strip("'")
    parsed = parse_skill_enrichment_result(result)
    logger.info("skill.completed", skill=skill_name, has_description=bool(parsed[0]))
    return parsed


def _enrich_ollama(mysql: MysqlUtil) -> int:
    return process_skill_enrichment(
        mysql,
        generate_skill_description_ollama,
        limit=get_enrich_limit(),
        check_empty_description_only=True,
    )


def _fetch_pending_skills(mysql: MysqlUtil, limit: int) -> List[Dict[str, str]]:
    where_clause = "ai_enriched = 0"
    query_find = f"SELECT name FROM job_skills WHERE {where_clause} LIMIT {limit}"
    rows = mysql.fetchAll(query_find)
    return [{'name': row[0]} for row in rows]


def _fetch_skill_context_safe(mysql: MysqlUtil, skill_name: str) -> str:
    try:
        return get_skill_context(mysql, skill_name)
    except Exception:
        return ""


def _save_skill_result(mysql: MysqlUtil, name: str, description: str, category: str):
    update_query = "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1 WHERE name = %s"
    mysql.executeAndCommit(update_query, [description, category, name])


def _enrich_huggingface(mysql: MysqlUtil) -> int:
    from ..llm_client import get_pipeline
    from ..llm_utils import process_batch

    batch_size = get_batch_size()
    limit = get_enrich_limit()

    skills = _fetch_pending_skills(mysql, limit)
    if not skills:
        return 0

    logger.info("skills.found", total=len(skills), batch_size=batch_size)

    pipe = get_pipeline()
    count = 0
    overall_start_time = time.time()

    for i in range(0, len(skills), batch_size):
        batch_items = skills[i:i + batch_size]
        processed_count = _process_skill_batch(
            mysql, pipe, batch_items, i, len(skills), count, overall_start_time
        )
        count += processed_count

    print("-" * 50)
    return count


def _process_skill_batch(
    mysql: MysqlUtil,
    pipeline: Any,
    batch_items: List[Dict[str, str]],
    start_idx: int,
    total: int,
    current_global_count: int,
    start_time: float
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
        context = _fetch_skill_context_safe(mysql, name)
        logger.info("skill.started", skill=name, index=current_idx, total=total)
        return build_skill_prompt_messages(name, context)

    def on_success(item: Dict[str, str], generated_text: str):
        nonlocal success_count
        name = item['name']
        description, category = parse_skill_enrichment_result(generated_text)
        if description and "Error" not in description:
            logger.info("skill.completed", skill=name, has_description=True, category=category)
            _save_skill_result(mysql, name, description, category)
            success_count += 1
        else:
            logger.warning("skill.failed_to_generate", skill=name)

    def on_error(item: Dict[str, str], ex: Exception):
        name = item['name']
        logger.error("skill.failed", skill=name, error=str(ex), traceback=traceback.format_exc())

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


def enrich_skills(mysql: MysqlUtil) -> int:
    backend = get_backend()
    if backend == "ollama":
        return _enrich_ollama(mysql)
    elif backend == "huggingface":
        return _enrich_huggingface(mysql)
    else:
        logger.error("unknown_backend", backend=backend)
        return 0
