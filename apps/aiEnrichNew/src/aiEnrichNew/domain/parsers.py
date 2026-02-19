import json
from typing import Dict, Any, Optional, Tuple
from commonlib.ai_helpers import rawToJson, validateResult
from commonlib.skill_enricher_service import parse_skill_llm_output as parse_skill_output_helper

def parse_job_enrichment_result(llm_output: str) -> Optional[Dict[str, Any]]:
    """
    Pure function to parse and validate job enrichment LLM output.
    Returns None if parsing fails or invalid.
    """
    try:
        # rawToJson and validateResult contain some printing/logging side effects
        # In a strict functional world we'd refactor them, but for now we wrap them.
        # They modify the dict in place (validateResult), which is a side effect on the object, 
        # but acceptable if we treat the dict as transient data.
        result = rawToJson(llm_output)
        if result is not None:
             validateResult(result)
             return result
        return None
    except Exception:
        # We might want to return a Result type (Success/Failure) instead of raising or printing here
        # to keep it pure. For now, letting exceptions bubble or returning None is pragmatic.
        raise

def parse_skill_enrichment_result(llm_output: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Pure function to parse skill enrichment LLM output.
    Returns (description, category).
    """
    result_str = llm_output.strip().strip('"').strip("'")
    return parse_skill_output_helper(result_str)
