import json
from unittest.mock import MagicMock

import pytest

from commonlib.ollama_client import OllamaResponse
from ..extraction_contract import (
    COMPANY_SCHEMA, ExtractionValidationError, MAX_COMPANY_LEN, parse_company_result, parse_extraction_result, query_and_parse, query_company,
)

sut = parse_extraction_result

VALID_RESULT = {
    "required_technologies": ["Java"],
    "optional_technologies": ["Docker"],
    "salary": "50000 EUR",
    "modality": "REMOTE",
}


def test_parses_valid_object():
    assert sut(json.dumps(VALID_RESULT)) == VALID_RESULT


def test_parses_json_code_fence():
    raw = f"```json\n{json.dumps(VALID_RESULT)}\n```"
    assert sut(raw) == VALID_RESULT


@pytest.mark.parametrize("raw, message", [
    pytest.param("", "empty", id="empty"),
    pytest.param('{"required_technologies": ["Java"],', "invalid JSON", id="truncated"),
    pytest.param(json.dumps({**VALID_RESULT, "modality": "ONSITE"}), "modality", id="invalid_modality"),
    pytest.param(json.dumps({**VALID_RESULT, "modality": '"REMOTE"'}), "modality", id="quoted_modality"),
    pytest.param(json.dumps({**VALID_RESULT, "extra": "value"}), "unexpected", id="extra_field"),
    pytest.param(json.dumps({**VALID_RESULT, "required_technologies": "Java"}), "array", id="string_technologies"),
    pytest.param(json.dumps({**VALID_RESULT, "required_technologies": [{"name": "Java"}]}), "array", id="nested_technologies"),
    pytest.param(json.dumps({**VALID_RESULT, "salary": {"min": 1}}), "salary", id="object_salary"),
    pytest.param('{"salary": "C:\\Users\\test", "required_technologies": []}', "invalid JSON", id="unescaped_path"),
])
def test_rejects_invalid_contract(raw, message):
    with pytest.raises(ExtractionValidationError, match=message):
        sut(raw)


def test_query_retries_invalid_response():
    valid = json.dumps(VALID_RESULT)
    query = MagicMock(side_effect=['{"required_technologies": ["Java"],', valid])
    result, response = query_and_parse(query, "prompt", max_attempts=2)
    assert result == VALID_RESULT
    assert response == valid
    assert query.call_count == 2
    assert "previous response was invalid" in query.call_args_list[1].args[0]


def test_query_retries_truncated_ollama_response():
    valid = json.dumps(VALID_RESULT)
    truncated = OllamaResponse(text=valid, url="http://ollama", done=True, done_reason="length")
    query = MagicMock(side_effect=[truncated, valid])
    result, response = query_and_parse(query, "prompt", max_attempts=2)
    assert result == VALID_RESULT
    assert response == valid


def test_query_returns_none_when_backend_is_unavailable():
    assert query_and_parse(MagicMock(return_value=None), "prompt") == (None, None)


class TestCompanyContract:
    @pytest.mark.parametrize("raw, expected", [
        pytest.param('{"company": "Acme"}', "Acme", id="company"),
        pytest.param('{"company": "  Acme S.L.  "}', "Acme S.L.", id="trimmed"),
        pytest.param('```json\n{"company": "Acme"}\n```', "Acme", id="code_fence"),
        pytest.param('{"company": "Acme", "extra": "value"}', "Acme", id="extra_field_ignored"),
    ])
    def test_parses_company(self, raw, expected):
        assert parse_company_result(raw) == expected

    @pytest.mark.parametrize("raw", [
        pytest.param('{"company": null}', id="null"),
        pytest.param('{"company": ""}', id="empty"),
        pytest.param('{"company": "   "}', id="blank"),
        pytest.param('{"company": "Unknown"}', id="unknown"),
        pytest.param('{"company": "unspecified"}', id="sentinel"),
        pytest.param('{"company": "N/A"}', id="n/a"),
    ])
    def test_returns_none_when_no_company(self, raw):
        assert parse_company_result(raw) is None

    @pytest.mark.parametrize("raw, message", [
        pytest.param("", "empty", id="empty"),
        pytest.param('{"company":', "invalid JSON", id="truncated"),
        pytest.param('["Acme"]', "JSON object", id="array"),
        pytest.param('{}', "missing fields", id="missing_company"),
        pytest.param('{"company": 42}', "string or null", id="number"),
    ])
    def test_rejects_invalid_company_contract(self, raw, message):
        with pytest.raises(ExtractionValidationError, match=message):
            parse_company_result(raw)

    def test_rejects_too_long_company(self):
        with pytest.raises(ExtractionValidationError, match="exceeds"):
            parse_company_result(json.dumps({"company": "x" * (MAX_COMPANY_LEN + 1)}))

    def test_company_schema_is_a_single_optional_field(self):
        assert COMPANY_SCHEMA["required"] == ["company"]
        assert COMPANY_SCHEMA["properties"]["company"]["type"] == ["string", "null"]

    def test_query_company_retries_invalid_response(self):
        valid = json.dumps({"company": "Acme"})
        query = MagicMock(side_effect=['{"company":', valid])
        company, response = query_company(query, "prompt", max_attempts=2)
        assert company == "Acme"
        assert query.call_count == 2

    def test_query_company_returns_none_when_backend_is_unavailable(self):
        assert query_company(MagicMock(return_value=None), "prompt") == (None, None)
