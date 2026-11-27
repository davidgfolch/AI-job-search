from structlog.testing import capture_logs
import pytest

from commonlib.ai_result_validation import (
    _expand_parenthesized_skills, _normalizeModality, flatten_skill_groups, listsToString, validateResult,
)
from commonlib.test.ai_helpers_fixtures import (
    LISTS_TO_STRING_CASES, LISTS_TO_STRING_TYPES_CASES, FLATTEN_STRING_CASES, FLATTEN_LIST_CASES,
    SALARY_CASES, CV_MATCH_CASES, MODALITY_CASES, EXPAND_CASES,
)


@pytest.mark.parametrize("value, expected", LISTS_TO_STRING_CASES)
def test_listsToString(value, expected):
    data = {"tech": value}
    listsToString(data, ["tech"])
    assert data["tech"] == expected


@pytest.mark.parametrize("data, expected", LISTS_TO_STRING_TYPES_CASES)
def test_listsToString_types(data, expected):
    listsToString(data, list(data))
    assert data == expected


@pytest.mark.parametrize("value, expected", FLATTEN_STRING_CASES)
def test_flatten_skill_groups_string(value, expected):
    assert flatten_skill_groups(value) == expected


@pytest.mark.parametrize("value, expected", FLATTEN_LIST_CASES)
def test_flatten_skill_groups_list(value, expected):
    assert flatten_skill_groups(value) == expected


@pytest.mark.parametrize("value", [123, None])
def test_flatten_skill_groups_invalid_type(value):
    assert flatten_skill_groups(value) == []


@pytest.mark.parametrize("value, expected", EXPAND_CASES)
def test__expand_parenthesized_skills(value, expected):
    assert _expand_parenthesized_skills(value) == expected


@pytest.mark.parametrize("input_data, expected_salary", SALARY_CASES)
def test_validateResult_salary(input_data, expected_salary):
    validateResult(input_data)
    assert input_data["salary"] == expected_salary


@pytest.mark.parametrize("input_data, expected_cv_match", CV_MATCH_CASES)
def test_validateResult_cv_match(input_data, expected_cv_match):
    validateResult(input_data)
    assert input_data["cv_match_percentage"] == expected_cv_match


@pytest.mark.parametrize("input_modality, expected", MODALITY_CASES)
def test_normalizeModality(input_modality, expected):
    result = {"modality": input_modality}
    _normalizeModality(result)
    assert result["modality"] == expected


@pytest.mark.parametrize("value, expected", [("remote", ["REMOTE"]), ("ONSITE", None), (["REMOTE", "hybrid"], ["REMOTE", "HYBRID"])])
def test_validateResult_normalizes_modality(value, expected):
    result = {"modality": value}
    validateResult(result)
    assert result["modality"] == expected


@pytest.mark.parametrize("value, expected", [
    ("3 days remote / 2 days office", "3 days remote / 2 days office"),
    ("  Hybrid, Full-time  ", "Hybrid, Full-time"),
    ("   ", None),
    ("", None),
    (None, None),
    ("x" * 600, "x" * 500),
])
def test_validateResult_normalizes_hybrid_info(value, expected):
    result = {"hybrid_info": value}
    validateResult(result)
    assert result["hybrid_info"] == expected


@pytest.mark.parametrize("echo", [
    "Hybrid work arrangement with days per week in the office or remote, schedule, or the exact hybrid wording stated in the text",
    "exact hybrid wording stated in the text",
    "days per week in the office or remote, schedule",
    "Días por semana en la oficina o en remoto, horario o la redacción exacta indicada en el texto",
])
def test_validateResult_drops_hybrid_info_that_echoes_the_prompt(echo):
    result = {"hybrid_info": echo}
    validateResult(result)
    assert result["hybrid_info"] is None


def test_validateResult_logs_dropped_hybrid_info_prompt_echo():
    with capture_logs() as records:
        validateResult({"hybrid_info": "exact hybrid wording stated in the text"})
    assert any(record["event"] == "ai.invalid_hybrid_info" and record.get("reason") == "prompt_echo" for record in records)


@pytest.mark.parametrize("value", [
    "3 days per week in the office, 2 days remote",
    "2 días en la oficina y 3 en remoto",
    "Hybrid, 2 days office / 3 days home office",
])
def test_validateResult_keeps_hybrid_arrangements(value):
    result = {"hybrid_info": value}
    validateResult(result)
    assert result["hybrid_info"] == value


def test_validateResult_skips_hybrid_info_when_absent():
    result = {}
    validateResult(result)
    assert "hybrid_info" not in result
