import json
from typing import Any, Callable

from commonlib.ai_helpers import VALID_MODALITIES


class ExtractionValidationError(ValueError):
    pass


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "required_technologies": {"type": "array", "items": {"type": "string"}},
        "optional_technologies": {"type": "array", "items": {"type": "string"}},
        "salary": {"type": ["string", "null"]},
        "modality": {"type": "string", "enum": sorted(VALID_MODALITIES)},
    },
    "required": ["required_technologies", "optional_technologies", "salary", "modality"],
    "additionalProperties": False,
}

_TECHNOLOGY_FIELDS = ("required_technologies", "optional_technologies")
_REQUIRED_FIELDS = (*_TECHNOLOGY_FIELDS, "salary", "modality")


def _strip_code_fence(value: str) -> str:
    if not value.startswith("```") or not value.endswith("```"):
        return value
    lines = value.splitlines()
    if lines and lines[0].strip().lower() in {"```json", "```"}:
        return "\n".join(lines[1:-1]).strip()
    return value


def validate_extraction_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise ExtractionValidationError("response must be a JSON object")
    missing = [field for field in _REQUIRED_FIELDS if field not in result]
    if missing:
        raise ExtractionValidationError(f"missing fields: {', '.join(missing)}")
    extra = [field for field in result if field not in _REQUIRED_FIELDS]
    if extra:
        raise ExtractionValidationError(f"unexpected fields: {', '.join(map(str, extra))}")
    for field in _TECHNOLOGY_FIELDS:
        values = result[field]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ExtractionValidationError(f"{field} must be an array of non-empty strings")
    salary = result["salary"]
    if salary is not None and not isinstance(salary, str):
        raise ExtractionValidationError("salary must be a string or null")
    if result["modality"] not in VALID_MODALITIES:
        raise ExtractionValidationError("modality must be REMOTE, HYBRID, or ON_SITE")
    return result


def parse_extraction_result(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ExtractionValidationError("response is empty")
    try:
        result = json.loads(_strip_code_fence(raw.strip()))
    except (TypeError, json.JSONDecodeError) as ex:
        raise ExtractionValidationError(f"invalid JSON: {getattr(ex, 'msg', str(ex))}") from ex
    return validate_extraction_result(result)


def query_and_parse(
    query: Callable[[str], Any], prompt: str, max_attempts: int = 2, log=None
) -> tuple[dict[str, Any] | None, Any]:
    attempts = max(1, max_attempts)
    for attempt in range(attempts):
        raw = query(prompt if attempt == 0 else f"{prompt}\n\nThe previous response was invalid. Return exactly one valid JSON object matching the requested structure.")
        if raw is None:
            return None, None
        try:
            if getattr(raw, "done_reason", None) == "length":
                raise ExtractionValidationError("response reached the output token limit")
            return parse_extraction_result(getattr(raw, "text", raw)), raw
        except ExtractionValidationError as ex:
            if attempt == attempts - 1:
                raise
            if log:
                log.warning("ai.structured_retry", attempt=attempt + 1, max_attempts=attempts, error=str(ex))
    return None, None
