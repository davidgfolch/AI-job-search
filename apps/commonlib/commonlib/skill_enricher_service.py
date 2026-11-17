import json
import re
from typing import Callable, List
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.skill_learning_path import URL_RE, dedupe_urls, split_learning_path_section
from commonlib.observability import get_logger

logger = get_logger("commonlib.skill_enricher_service")

DESCRIPTION_UPDATE = "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1 WHERE name = %s"
DESCRIPTION_AND_PATH_UPDATE = (
    "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1, "
    "learning_path = CASE WHEN (learning_path IS NULL OR JSON_LENGTH(learning_path) = 0) "
    "THEN %s ELSE learning_path END WHERE name = %s"
)

def log_no_pending_skills(limit: int) -> None:
    """The one record an idle skill cycle logs, shared by the ollama and huggingface paths."""
    logger.info("jobs.skipped", message="No skills pending.", reason="no_pending_skills", limit=limit)

def process_skill_enrichment(
    mysql: MysqlUtil,
    generate_description_fn: Callable[[str, str], tuple[str, str]],
    limit: int = 10,
    check_empty_description_only: bool = True
) -> int:
    """
    Common logic for skill enrichment.
    
    :param mysql: MysqlUtil instance
    :param generate_description_fn: Function that takes (skill_name, context) and returns (description, category)
    :param limit: limit of skills to process
    :param check_empty_description_only: if True, filters by description IS NULL OR description = ''. 
                                         If False, only filters by ai_enriched (NULL treated as not enriched).
    """
    from commonlib.stopWatch import StopWatch

    where_clause = "COALESCE(ai_enriched, 0) = 0"
    if check_empty_description_only:
        where_clause += " AND (description IS NULL OR description = '')"
    else:
        # If we are not checking for empty description, implies we might re-enrich or enrich regardless of existing desc if ai_enriched=0
        pass
    query_find = f"SELECT name FROM job_skills WHERE {where_clause} LIMIT {limit}"
    rows = mysql.fetchAll(query_find)
    if not rows:
        log_no_pending_skills(limit)
        return 0
    logger.info("skill.enrich_started", count=len(rows), limit=limit, check_empty_description_only=check_empty_description_only)
    
    count = 0
    stop_watch = StopWatch()
    
    for i, row in enumerate(rows):
        stop_watch.start()
        name = row[0]
        current_idx = i + 1
        total = len(rows)
        # Determine context length for logging (approximate input length)
        # We don't have the exact prompt here but we can log the context size
        context = ""
        try:
            context = get_skill_context(mysql, name)
        except Exception:
            pass # context fetching fail shouldn't stop flow
            
        logger.debug("skill.enriching", index=current_idx, total=total, name=name, input_length=len(context) + len(name))

        try:
            # Re-fetch context inside try block to be safe, though duplicate
            # context = get_skill_context(mysql, name) # Already fetched above
            result = generate_description_fn(name, context)
            normalized = _normalize_generation_result(result)
            if normalized is None:
                logger.warning("skill.invalid_result", name=name, result_type=type(result).__name__)
                continue
            description, category, learning_path = normalized
            if description and "Error" not in description:
                # Log Result
                result_log = {
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "category": category,
                    "learning_path": len(learning_path)
                }
                logger.debug("skill.enriched", name=name, result=result_log)
                fields = ["description", "category"] + (["learning_path"] if learning_path else [])
                logger.debug("skill.persisting", name=name, fields=fields)
                if learning_path:
                    mysql.executeAndCommit(DESCRIPTION_AND_PATH_UPDATE, [description, category, json.dumps(learning_path), name])
                else:
                    mysql.executeAndCommit(DESCRIPTION_UPDATE, [description, category, name])
                count += 1
            else:
                logger.warning("skill.description_failed", name=name)
        except Exception:
            logger.exception("skill.enrich_failed", name=name)
        stop_watch.end()
        logger.debug("skill.iteration_completed", index=current_idx, total=total)
    logger.info("skill.enrich_completed", updated=count, count=len(rows))
    return count

def parse_skill_llm_output(result: str) -> tuple[str, str, List[str]]:
    """
    Parses the LLM output into (description, category, learning_path).
    Robust against various formatting issues; the Learning Path section is removed
    before the description/category split so its URLs never leak into the description.
    """
    result, learning_path_body = split_learning_path_section(result)
    learning_path = dedupe_urls(URL_RE.findall(learning_path_body)) if learning_path_body else []
    category = "Other"
    description = result
    # Try to find "Category: ..." pattern
    # Case insensitive, handles bolding/markdown like **Category**: or ## Category:
    match = re.search(r'(?:^|\n)[#*]*\s*Category\s*[#*]*\s*:\s*(.+)', result, re.IGNORECASE)
    if match:
        category_part = match.group(1).strip()
        # Clean up if it captured too much (e.g. end of line): keep only the first line
        category_part = category_part.split('\n')[0].strip()
        # Remove common markdown clutter
        category = category_part.replace('*', '').replace('`', '').strip()

        # Split description to be everything BEFORE the category line
        # If Category is at the start, take everything AFTER it instead
        start_index = match.start()
        if start_index == 0:
            description = result[match.end():].strip()
        else:
            description = result[:start_index].strip()
    return description, category, learning_path


def _normalize_generation_result(result) -> tuple[str, str | None, List[str]] | None:
    """Accepts the (description, category[, learning_path]) tuple or a bare description string."""
    if isinstance(result, tuple) and len(result) in (2, 3):
        description, category = result[0], result[1]
        learning_path = result[2] if len(result) == 3 else []
        return description, category, list(learning_path or [])
    if isinstance(result, str):
        return result, None, []
    return None

