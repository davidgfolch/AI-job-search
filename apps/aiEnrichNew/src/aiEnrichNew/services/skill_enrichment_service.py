import time
import json
import traceback
from typing import List, Dict, Any, Callable

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.terminalColor import yellow, magenta, cyan, red, green
from commonlib.environmentUtil import getEnvBool, getEnv
from commonlib.stopWatch import StopWatch
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.observability import get_logger

from ..config import get_batch_size, get_enrich_timeout_skill
from ..llm_utils import process_batch
from ..domain.mappers import build_skill_prompt_messages
from ..domain.parsers import parse_skill_enrichment_result

logger = get_logger("aiEnrichNew.skill_enrichment")


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


def enrich_skills(mysql: MysqlUtil, pipeline: Any) -> int:
    if not getEnvBool("AI_ENRICHNEW_SKILL", True):
        return 0

    batch_size = get_batch_size()
    limit = int(getEnv('AI_ENRICHNEW_SKILL_ENRICH_LIMIT', str(batch_size)))

    skills = _fetch_pending_skills(mysql, limit)
    if not skills:
        return 0

    logger.info("skills.found", total=len(skills), batch_size=batch_size)

    count = 0
    overall_start_time = time.time()

    for i in range(0, len(skills), batch_size):
        batch_items = skills[i:i + batch_size]
        processed_count = _process_skill_batch_pipeline(
            mysql,
            pipeline,
            batch_items,
            i,
            len(skills),
            count,
            overall_start_time
        )
        count += processed_count

    print("-" * 50)
    return count


def _process_skill_batch_pipeline(
    mysql: MysqlUtil,
    pipeline: Any,
    batch_items: List[Dict[str, str]],
    start_idx: int,
    total: int,
    current_global_count: int,
    start_time: float
) -> int:
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
        get_enrich_timeout_skill(),
        "skills"
    )

    stop_watch_batch.end()
    return success_count
