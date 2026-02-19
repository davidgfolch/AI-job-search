from typing import Tuple, Dict, Any, Optional
from commonlib.ai_helpers import mapJob
from ..config import get_job_system_prompt, get_skill_system_prompt, get_input_max_len

def map_db_job_to_domain(job_row: Any) -> Dict[str, Any]:
    """
    Pure function to map a DB job row to a domain dictionary.
    """
    id = job_row[0]
    # Reusing existing mapJob helper for title/company/markdown extraction logic
    # ideally mapJob should also be pure and here, but preventing code duplication for now.
    title, company, markdown = mapJob(job_row)
    return {
        'id': id,
        'title': title,
        'company': company,
        'markdown': markdown,
        'length': len(markdown)
    }

def build_job_prompt_messages(job: Dict[str, Any]) -> list[dict]:
    """
    Pure function to build chat messages for job enrichment.
    """
    title = job['title']
    markdown = job['markdown']
    
    # Truncate
    max_len = get_input_max_len()
    if len(markdown) > max_len:
        markdown = markdown[:max_len] + "...(truncated)"
        
    user_message = f"Job Title: {title}\n\nDescription:\n{markdown}"
    return [
        {"role": "system", "content": get_job_system_prompt()},
        {"role": "user", "content": user_message}
    ]

def build_skill_prompt_messages(skill_name: str, context: str) -> list[dict]:
    """
    Pure function to build chat messages for skill enrichment.
    """
    context_str = f"\nContext (related technologies found in jobs): {context}" if context else ""
    user_message = f"Skill: {skill_name}{context_str}\n\nProvide a deep technical description."
    return [
        {"role": "system", "content": get_skill_system_prompt()},
        {"role": "user", "content": user_message}
    ]
