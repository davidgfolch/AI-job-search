from typing import Callable
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.observability import get_logger

logger = get_logger("commonlib.skill_enricher_service")

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
                                         If False, only filters by ai_enriched = 0.
    """
    from commonlib.stopWatch import StopWatch
    from datetime import datetime

    where_clause = "ai_enriched = 0"
    if check_empty_description_only:
        where_clause += " AND (description IS NULL OR description = '')"
    else:
        # If we are not checking for empty description, implies we might re-enrich or enrich regardless of existing desc if ai_enriched=0
        pass
    query_find = f"SELECT name FROM job_skills WHERE {where_clause} LIMIT {limit}"
    rows = mysql.fetchAll(query_find)
    if not rows:
        logger.info("skill.enrich_skipped", message="No skills pending.", reason="no_pending_skills", limit=limit)
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
            description = ""
            category = None
            if isinstance(result, tuple) and len(result) == 2:
                description, category = result
            elif isinstance(result, str):
                description = result
                category = None
            else:
                logger.warning("skill.invalid_result", name=name, result_type=type(result).__name__)
                continue
            if description and "Error" not in description:
                # Log Result
                result_log = {
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "category": category
                }
                logger.debug("skill.enriched", name=name, result=result_log)
                logger.debug("skill.persisting", name=name, fields=["description", "category"])
                update_query = "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1 WHERE name = %s"
                mysql.executeAndCommit(update_query, [description, category, name])
                count += 1
            else:
                logger.warning("skill.description_failed", name=name)
        except Exception:
            logger.exception("skill.enrich_failed", name=name)
        stop_watch.end()
        logger.debug("skill.iteration_completed", index=current_idx, total=total)
    logger.info("skill.enrich_completed", updated=count, count=len(rows))
    return count

def parse_skill_llm_output(result: str) -> tuple[str, str]:
    """
    Parses the LLM output to extract description and category.
    Robust against various formatting issues.
    """
    import re
    category = "Other"
    description = result
    # Try to find "Category: ..." pattern
    # Case insensitive, handles bolding/markdown like **Category**: or ## Category:
    match = re.search(r'(?:^|\n)[#*]*\s*Category\s*[#*]*\s*:\s*(.+)', result, re.IGNORECASE)
    if match:
        category_part = match.group(1).strip()
        # Clean up if there are trailing characters or it captured too much (e.g. end of line)
        # Just take the first line of the matched group
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
    return description, category
