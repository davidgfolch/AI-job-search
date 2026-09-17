import pytest
from unittest.mock import patch, MagicMock

from commonlib.test.ollama_constants import OLLAMA_TEST_URL, OLLAMA_DOCKER_TEST_URL
from commonlib.ollama_client import ping_ollama, query_ollama, resolve_ollama_url, _strip_provider_prefix
from commonlib.ollama_config import OLLAMA_HOST_FROM_DOCKER_BASE_URL


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    monkeypatch.setattr("commonlib.ollama_client.time.sleep", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def clean_max_new_tokens(monkeypatch):
    monkeypatch.delenv("AI_ENRICH_MAX_NEW_TOKENS", raising=False)
    monkeypatch.delenv("AI_ENRICHSKILL_MAX_NEW_TOKENS", raising=False)


class TestQueryOllama:

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_success(self, mock_post, mock_candidates):
        mock_post.return_value.json.return_value = {"response": '{"key": "value"}'}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("test prompt")

        assert result == '{"key": "value"}'
        mock_post.assert_called_once()

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_success_no_json_mode(self, mock_post, mock_candidates):
        mock_post.return_value.json.return_value = {"response": "plain text"}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("test prompt", json_mode=False)

        assert result == "plain text"
        call_kwargs = mock_post.call_args[1]
        assert "format" not in call_kwargs["json"]

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_json_mode_adds_format(self, mock_post, mock_candidates):
        mock_post.return_value.json.return_value = {"response": "{}"}
        mock_post.return_value.raise_for_status.return_value = None

        query_ollama("prompt", json_mode=True)

        assert mock_post.call_args[1]["json"]["format"] == "json"

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_empty_response_field(self, mock_post, mock_candidates):
        mock_post.return_value.json.return_value = {}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("prompt")

        assert result == ""

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_all_failures_return_none(self, mock_post, mock_candidates):
        mock_post.side_effect = Exception("fail")

        result = query_ollama("prompt")

        assert result is None
        assert mock_post.call_count == 3

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_succeeds_on_second_retry(self, mock_post, mock_candidates):
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

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.post")
    def test_custom_parameters(self, mock_post, mock_candidates):
        mock_post.return_value.json.return_value = {"response": "result"}
        mock_post.return_value.raise_for_status.return_value = None

        result = query_ollama("prompt", model="ollama/custom-model", primary_url="http://custom:11434", timeout=30)

        assert result == "result"
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["model"] == "custom-model"
        assert call_kwargs["timeout"] == 30
        assert call_kwargs["json"]["options"]["temperature"] == 0
        assert call_kwargs["json"]["options"]["num_predict"] == 2048

    @patch("commonlib.ollama_client.requests.post")
    def test_base_url_trailing_slash_stripped(self, mock_post):
        mock_post.return_value.json.return_value = {"response": "x"}
        mock_post.return_value.raise_for_status.return_value = None

        query_ollama("prompt", primary_url=f"{OLLAMA_TEST_URL}/")

        assert mock_post.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/generate"

    @patch("commonlib.ollama_client.requests.post")
    def test_raises_for_status_triggers_retry(self, mock_post):
        response_mock = MagicMock()
        response_mock.raise_for_status.side_effect = Exception("HTTP 500")
        mock_post.return_value = response_mock

        result = query_ollama("prompt")

        assert result is None
        assert mock_post.call_count == 9

    @patch("commonlib.ollama_client.requests.post")
    def test_falls_back_to_next_candidate_when_primary_down(self, mock_post):
        down_response = MagicMock()
        down_response.raise_for_status.side_effect = Exception("down")
        ok_response = MagicMock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {"response": "host result"}
        mock_post.side_effect = [down_response, down_response, down_response, ok_response]

        result = query_ollama("prompt", primary_url=OLLAMA_DOCKER_TEST_URL)

        assert result == "host result"
        assert mock_post.call_count == 4
        assert mock_post.call_args[0][0] == f"{OLLAMA_HOST_FROM_DOCKER_BASE_URL}/api/generate"


class TestPingOllama:

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.get")
    def test_success(self, mock_get, mock_candidates):
        mock_get.return_value.raise_for_status.return_value = None
        assert ping_ollama() is True
        mock_get.assert_called_once_with(f"{OLLAMA_TEST_URL}/api/tags", timeout=5)

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.get")
    def test_failure_returns_false(self, mock_get, mock_candidates):
        mock_get.side_effect = Exception("Connection refused")
        assert ping_ollama(timeout=2) is False

    @patch("commonlib.ollama_client.requests.get")
    def test_trailing_slash_stripped(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        ping_ollama(primary_url=f"{OLLAMA_TEST_URL}/")
        assert mock_get.call_args[0][0] == f"{OLLAMA_TEST_URL}/api/tags"

    @patch("commonlib.ollama_client.requests.get")
    def test_falls_back_to_host_when_docker_down(self, mock_get):
        ok_response = MagicMock()
        ok_response.raise_for_status.return_value = None
        mock_get.side_effect = [Exception("down"), ok_response]

        assert ping_ollama(primary_url=OLLAMA_DOCKER_TEST_URL) is True
        assert mock_get.call_count == 2
        assert mock_get.call_args[0][0] == f"{OLLAMA_HOST_FROM_DOCKER_BASE_URL}/api/tags"


class TestResolveOllamaUrl:

    @patch("commonlib.ollama_client._candidate_urls", return_value=(OLLAMA_TEST_URL,))
    @patch("commonlib.ollama_client.requests.get")
    def test_returns_candidate_url(self, mock_get, mock_candidates):
        mock_get.return_value.raise_for_status.return_value = None
        assert resolve_ollama_url() == OLLAMA_TEST_URL
        mock_get.assert_called_once_with(f"{OLLAMA_TEST_URL}/api/tags", timeout=5)

    @patch("commonlib.ollama_client.requests.get")
    def test_returns_none_when_all_fail(self, mock_get):
        mock_get.side_effect = Exception("down")
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL, timeout=2) is None

    @patch("commonlib.ollama_client.requests.get")
    def test_returns_fallback_url_when_primary_down(self, mock_get):
        ok = MagicMock()
        ok.raise_for_status.return_value = None
        mock_get.side_effect = [Exception("down"), ok]
        assert resolve_ollama_url(primary_url=OLLAMA_DOCKER_TEST_URL) == OLLAMA_HOST_FROM_DOCKER_BASE_URL
        assert mock_get.call_count == 2


class TestStripProviderPrefix:

    def test_strips_ollama_prefix(self):
        assert _strip_provider_prefix("ollama/qwen2.5:3b") == "qwen2.5:3b"

    def test_strips_any_prefix(self):
        assert _strip_provider_prefix("openai/gpt-4") == "gpt-4"

    def test_no_prefix(self):
        assert _strip_provider_prefix("qwen2.5:3b") == "qwen2.5:3b"