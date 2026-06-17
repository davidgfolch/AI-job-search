import pytest
from unittest.mock import patch, MagicMock
from ..ollama_client import ping_ollama, query_ollama, _strip_provider_prefix


class TestQueryOllama:

    @patch("aiEnrich.ollama_client.requests.post")
    def test_success(self, mock_post):
        mock_post.return_value.json.return_value = {"response": '{"key": "value"}'}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("test prompt")

        assert result == '{"key": "value"}'
        mock_post.assert_called_once()

    @patch("aiEnrich.ollama_client.requests.post")
    def test_success_no_json_mode(self, mock_post):
        mock_post.return_value.json.return_value = {"response": "plain text"}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("test prompt", json_mode=False)

        assert result == "plain text"
        call_kwargs = mock_post.call_args[1]
        assert "format" not in call_kwargs["json"]

    @patch("aiEnrich.ollama_client.requests.post")
    def test_json_mode_adds_format(self, mock_post):
        mock_post.return_value.json.return_value = {"response": "{}"}
        mock_post.return_value.raise_for_status.return_value = None

        query_ollama("prompt", json_mode=True)

        assert mock_post.call_args[1]["json"]["format"] == "json"

    @patch("aiEnrich.ollama_client.requests.post")
    def test_empty_response_field(self, mock_post):
        mock_post.return_value.json.return_value = {}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("prompt")

        assert result == ""

    @patch("aiEnrich.ollama_client.requests.post")
    def test_all_failures_return_none(self, mock_post):
        mock_post.side_effect = Exception("fail")

        result = query_ollama("prompt")

        assert result is None
        assert mock_post.call_count == 3

    @patch("aiEnrich.ollama_client.requests.post")
    def test_succeeds_on_second_retry(self, mock_post):
        success_response = MagicMock()
        success_response.json.return_value = {"response": "ok"}
        success_response.raise_for_status.return_value = None
        mock_post.side_effect = [
            Exception("first fail"),
            success_response,
        ]

        result = query_ollama("prompt")

        assert result == "ok"
        assert mock_post.call_count == 2

    @patch("aiEnrich.ollama_client.requests.post")
    def test_custom_parameters(self, mock_post):
        mock_post.return_value.json.return_value = {"response": "result"}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("prompt", model="ollama/custom-model", base_url="http://custom:11434", timeout=30)

        assert result == "result"
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["model"] == "custom-model"
        assert call_kwargs["timeout"] == 30
        assert call_kwargs["json"]["options"]["temperature"] == 0
        assert call_kwargs["json"]["options"]["num_predict"] == 2048

    @patch("aiEnrich.ollama_client.requests.post")
    def test_base_url_trailing_slash_stripped(self, mock_post):
        mock_post.return_value.json.return_value = {"response": "x"}
        mock_post.return_value.raise_for_status.return_value = None

        query_ollama("prompt", base_url="http://localhost:11434/")

        assert mock_post.call_args[0][0] == "http://localhost:11434/api/generate"

    @patch("aiEnrich.ollama_client.requests.post")
    def test_raises_for_status_triggers_retry(self, mock_post):
        response_mock = MagicMock()
        response_mock.raise_for_status.side_effect = Exception("HTTP 500")
        mock_post.return_value = response_mock

        result = query_ollama("prompt")

        assert result is None
        assert mock_post.call_count == 3


class TestPingOllama:

    @patch("aiEnrich.ollama_client.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        assert ping_ollama("http://localhost:11434") is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)

    @patch("aiEnrich.ollama_client.requests.get")
    def test_failure_returns_false(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        assert ping_ollama("http://localhost:11434", timeout=2) is False

    @patch("aiEnrich.ollama_client.requests.get")
    def test_trailing_slash_stripped(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        ping_ollama("http://localhost:11434/")
        assert mock_get.call_args[0][0] == "http://localhost:11434/api/tags"

    @patch("aiEnrich.ollama_client.requests.get")
    def test_custom_timeout(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        ping_ollama("http://ollama:11434", timeout=10)
        mock_get.assert_called_once_with("http://ollama:11434/api/tags", timeout=10)


class TestStripProviderPrefix:

    def test_strips_ollama_prefix(self):
        assert _strip_provider_prefix("ollama/qwen2.5:3b") == "qwen2.5:3b"

    def test_strips_any_prefix(self):
        assert _strip_provider_prefix("openai/gpt-4") == "gpt-4"

    def test_no_prefix(self):
        assert _strip_provider_prefix("qwen2.5:3b") == "qwen2.5:3b"
