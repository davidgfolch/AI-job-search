import pytest
from unittest.mock import patch
from ..parsers import parse_job_enrichment_result


@pytest.mark.parametrize("raw_return, validate_side_effect, expected", [
    pytest.param({"key": "value"}, None, {"key": "value"}, id="success"),
    pytest.param(None, None, None, id="none_return"),
    pytest.param(Exception("Parsing error"), None, Exception, id="exception"),
])
@patch("aiEnrichNew.domain.parsers.rawToJson")
@patch("aiEnrichNew.domain.parsers.validateResult")
def test_parse_job_enrichment_result(mock_validate, mock_rawToJson, raw_return, validate_side_effect, expected):
    if isinstance(raw_return, Exception):
        mock_rawToJson.side_effect = raw_return
    else:
        mock_rawToJson.return_value = raw_return
        mock_validate.side_effect = validate_side_effect

    if expected is Exception:
        with pytest.raises(Exception):
            parse_job_enrichment_result("bad content")
    else:
        result = parse_job_enrichment_result("some json")
        assert result == expected
        if expected is not None:
            mock_validate.assert_called_with(expected)
