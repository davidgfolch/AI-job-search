import traceback
from typing import Callable
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.terminalColor import yellow, magenta, cyan, red

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
    where_clause = "ai_enriched = 0"
    if check_empty_description_only:
        where_clause += " AND (description IS NULL OR description = '')"
    else:
        # If we are not checking for empty description, implies we might re-enrich or enrich regardless of existing desc if ai_enriched=0
        pass
    query_find = f"SELECT name FROM job_skills WHERE {where_clause} LIMIT {limit}"
    rows = mysql.fetchAll(query_find)
    if not rows:
        print(magenta("No skills to enrich. "), end='')
        return 0
    print(cyan(f"Found {len(rows)} skills to enrich..."))
    count = 0
    for row in rows:
        name = row[0]
        print("Enriching skill: ", yellow(name))
        try:
            context = get_skill_context(mysql, name)
            result = generate_description_fn(name, context)
            # Handle both tuple (desc, cat) and old string format for backward compatibility if needed, 
            # though we are changing the implementation so we can enforce tuple.
            description = ""
            category = None
            if isinstance(result, tuple) and len(result) == 2:
                description, category = result
            elif isinstance(result, str):
                description = result
                category = None
            else:
                print(yellow(f"Invalid result format for {name}: {type(result)}"))
                continue
            # Simple validation: valid description and not an error string if API returns one
            if description and "Error" not in description:
                print("Description: ", magenta(description[:50] + "..."))
                if category:
                    print("Category: ", magenta(category))
                update_query = "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1 WHERE name = %s"
                mysql.executeAndCommit(update_query, [description, category, name])
                count += 1
            else:
                print(yellow(f"Failed to generate description for {name}"))
        except Exception as e:
            print(yellow(f"Error enriching skill {name}"))
            print(red(traceback.format_exc()))
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
        # This is a bit heuristic; if Category is at the end, we take everything before it.
        # Find the start index of the match in the original string
        start_index = match.start()
        description = result[:start_index].strip()
    
    return description, category
