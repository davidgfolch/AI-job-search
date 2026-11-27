"""Normalization and validation of an AI extraction result before it is stored.

Split out of `ai_helpers`: the extraction contract, the enrich/retry loops and the tests
share one definition of what a valid result looks like (salary, technologies, modality,
hybrid detail, cv match), so the rules live here and `ai_helpers` re-exports them.
"""
import re

from commonlib.stringUtil import hasLen
from commonlib.modality_extractor import MODALITIES, normalize_modalities
from commonlib.observability import get_logger

logger = get_logger("commonlib.ai_result_validation")

MAX_HYBRID_INFO_LEN = 500
# Fragments of the extraction instructions. When the model states no arrangement it sometimes
# echoes this wording instead of describing the offer, so such a value is discarded rather than
# stored and rendered as if the offer had said it. The wording is checked case-insensitively.
HYBRID_INFO_PROMPT_ECHO_PHRASES = (
    "exact hybrid wording",
    "offer's own hybrid wording",
    "hybrid arrangement stated in the text",
    "stated in the text",
    "in the office or remote, schedule",
    "offer's language",
    "repeat or paraphrase",
    "must be a string or null",
    "when the offer allows hybrid work",
    "states no arrangement details",
    "días por semana en la oficina o en remoto, horario",
    "redacción exacta",
    "indicada en el texto",
    "idioma de la oferta",
)

VALID_MODALITIES = set(MODALITIES)

SALARY_LABEL_REGEX = r'^(sueldo|salarios?|\(?según experiencia\)?)[: ]+(.+)'


def _normalizeModality(result: dict) -> None:
    result['modality'] = normalize_modalities(result.get('modality')) or None


def is_hybrid_info_prompt_echo(value: str) -> bool:
    """True when the hybrid detail repeats the extraction instructions instead of the offer."""
    normalized = " ".join(str(value or "").casefold().replace("’", "'").split())
    return any(phrase in normalized for phrase in HYBRID_INFO_PROMPT_ECHO_PHRASES)


def _normalize_hybrid_info(result: dict) -> None:
    """Trim the extracted hybrid detail, capping it at the DB column size.
    Blank values and prompt echoes become `None` so the job detail never shows
    the instructions as if they were the offer's arrangement.
    """
    if 'hybrid_info' not in result:
        return
    value = result.get('hybrid_info')
    if not isinstance(value, str):
        result['hybrid_info'] = None
        return
    value = value.strip()[:MAX_HYBRID_INFO_LEN]
    if is_hybrid_info_prompt_echo(value):
        logger.warning("ai.invalid_hybrid_info", reason="prompt_echo")
        value = ""
    result['hybrid_info'] = value or None


def _normalize_salary(result: dict) -> None:
    salary = result.get('salary')
    if not salary:  # infojobs
        return
    if isinstance(salary, dict):
        if 'min' in salary and 'max' in salary:
            salary = f"{salary.get('min')}-{salary.get('max')}"
        elif 'amount' in salary:
            val = salary.get('amount')
            salary = str(val) if val is not None else None
        else:
            salary = str(salary)
        result['salary'] = salary
    elif salary is not None and not isinstance(salary, str):
        salary = str(salary)
    if salary and re.match(r'^[^0-9]+$', salary):  # doesn't contain numbers
        logger.warning("ai.invalid_salary", reason="no_numbers", salary=salary)
        result.update({'salary': None})
    elif salary:
        if hasLen(re.finditer(SALARY_LABEL_REGEX, salary, flags=re.I)):
            result.update({'salary': re.sub(SALARY_LABEL_REGEX, r'\2', salary, flags=re.I)})


def _validate_cv_match(result: dict) -> None:
    cv_match = result.get('cv_match_percentage')
    if not cv_match:
        return
    try:
        match_value = int(cv_match)
        if match_value < 0 or match_value > 100:
            logger.warning("ai.invalid_cv_match", reason="out_of_range", cv_match_percentage=cv_match)
            result.update({'cv_match_percentage': None})
    except (ValueError, TypeError):
        logger.warning("ai.invalid_cv_match", reason="not_a_number", cv_match_percentage=cv_match)
        result.update({'cv_match_percentage': None})


def validateResult(result: dict[str, str]):
    _normalize_salary(result)
    listsToString(result, ['required_technologies', 'optional_technologies'])
    if not result.get('required_technologies') and not result.get('optional_technologies'):
        logger.warning("ai.no_technologies", reason="both_technology_fields_empty")
    _normalizeModality(result)
    _normalize_hybrid_info(result)
    _validate_cv_match(result)


def _expand_parenthesized_skills(value: str) -> str:
    pattern = r"(\w[\w\s\-#+.]*)\s*\(([^)]+)\)"
    while re.search(pattern, value):
        value = re.sub(pattern, lambda m: f"{m.group(1).strip()}, {', '.join(x.strip() for x in m.group(2).split(','))}", value)
        value = re.sub(r", *,", ",", value)
    return value


def flatten_skill_groups(value) -> list[str]:
    if isinstance(value, str):
        value = _expand_parenthesized_skills(value)
        items = [x.strip() for x in value.split(",")]
    elif isinstance(value, list):
        items = []
        for item in value:
            if item is None:
                continue
            expanded = _expand_parenthesized_skills(str(item).strip())
            items.extend(x.strip() for x in expanded.split(","))
    else:
        items = []
    return list(dict.fromkeys([x for x in items if x]))


def listsToString(result: dict[str, str], fields: list[str]):
    for f in fields:
        value = result.get(f, None)
        if not value:
            result[f] = None
        else:
            unique_items = flatten_skill_groups(value)
            if unique_items:
                result[f] = ",".join(unique_items)
                if result[f].lower() in ['none specified', 'null']:
                    result[f]=None
            else:
                result[f] = None
