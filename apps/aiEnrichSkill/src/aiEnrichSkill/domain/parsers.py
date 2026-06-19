from typing import Tuple, Optional
from commonlib.skill_enricher_service import parse_skill_llm_output


def parse_skill_enrichment_result(llm_output: str) -> Tuple[Optional[str], Optional[str]]:
    result_str = llm_output.strip().strip('"').strip("'")
    return parse_skill_llm_output(result_str)
