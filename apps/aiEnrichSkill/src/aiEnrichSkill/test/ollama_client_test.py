import pytest
from unittest.mock import patch, MagicMock

from ..ollama_client import ping_ollama, query_ollama, _strip_provider_prefix


@pytest.mark.parametrize("model, expected", [
    pytest.param("ollama/llama3.2", "llama3.2", id="with_prefix"),
    pytest.param("llama3.2", "llama3.2", id="no_prefix"),
])
def test_strip_provider_prefix(model, expected):
    assert _strip_provider_prefix(model) == expected


@pytest.mark.parametrize("side_effect, expected", [
    pytest.param(None, True, id="success"),
    pytest.param(Exception("Connection refused"), False, id="failure"),
])
@patch("aiEnrichSkill.ollama_client.requests.get")
def test_ping_ollama(mock_get, side_effect, expected):
    if side_effect:
        mock_get.side_effect = side_effect
    else:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

    result = ping_ollama("http://localhost:11434", timeout=5)
    assert result is expected


@patch("aiEnrichSkill.ollama_client.requests.post")
def test_query_ollama_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "This is a skill description"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = query_ollama("Describe Python", model="ollama/qwen2.5:3b", timeout=90, json_mode=False)
    assert result == "This is a skill description"


@patch("aiEnrichSkill.ollama_client.requests.post")
def test_query_ollama_failure_all_retries(mock_post):
    mock_post.side_effect = Exception("Server error")

    result = query_ollama("Describe Python", timeout=5, json_mode=False)
    assert result is None
    assert mock_post.call_count == 3
