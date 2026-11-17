from typing import List, Optional, Tuple
from commonlib.skill_enricher_service import parse_skill_llm_output
from commonlib.skill_learning_path import parse_learning_path_urls


def parse_skill_enrichment_result(llm_output: str) -> Tuple[Optional[str], Optional[str], List[str]]:
    result_str = llm_output.strip().strip('"').strip("'")
    return parse_skill_llm_output(result_str)


def parse_learning_path_result(llm_output: str) -> List[str]:
    return parse_learning_path_urls(llm_output.strip().strip('"').strip("'"))
