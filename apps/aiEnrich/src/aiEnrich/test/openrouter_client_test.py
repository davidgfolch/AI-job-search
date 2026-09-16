import pytest
from unittest.mock import patch, MagicMock

from ..openrouter_client import ping_openrouter, query_openrouter, DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_FALLBACK_MODEL
from ._client_mocks import make_choice_response, make_sequence_choices


class TestQueryOpenrouter:

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_success(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response('{"key": "value"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            result = query_openrouter("test prompt")
        assert result == '{"key": "value"}'
        mock_openai_class.assert_called_with(base_url=DEFAULT_BASE_URL, api_key="sk-test", timeout=90)

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_uses_custom_model_and_base_url(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response('{"key": "value"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            result = query_openrouter("prompt", model="anthropic/claude-3.5-sonnet", base_url="http://custom:11434", timeout=30)
        assert result == '{"key": "value"}'
        call_kwargs = mock_openai_class.return_value.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "anthropic/claude-3.5-sonnet"
        assert call_kwargs["max_tokens"] == 2048
        assert call_kwargs["temperature"] == 0
        assert mock_openai_class.call_args[1]["base_url"] == "http://custom:11434"
        assert mock_openai_class.call_args[1]["timeout"] == 30

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_json_mode_adds_response_format(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response("{}")
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            query_openrouter("prompt", json_mode=True)
        assert mock_openai_class.return_value.chat.completions.create.call_args[1]["response_format"] == {"type": "json_object"}

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_json_mode_disabled_omits_response_format(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response('{"key": "value"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            query_openrouter("prompt", json_mode=False)
        assert "response_format" not in mock_openai_class.return_value.chat.completions.create.call_args[1]

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_all_failures_return_none(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        mock_openai_class.return_value.chat.completions.create.side_effect = Exception("fail")
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            result = query_openrouter("prompt")
        assert result is None
        assert mock_openai_class.return_value.chat.completions.create.call_count == 3

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_invalid_json_retries_then_falls_back(self, mock_openai_class):
        mock_openai_class.return_value = make_sequence_choices(
            "User Safety: safe", "User Safety: safe", "User Safety: safe", '{"salary": "100k"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            with patch("aiEnrich.openrouter_client.time.sleep"):
                result = query_openrouter("prompt", fallback_model=DEFAULT_FALLBACK_MODEL)
        assert result == '{"salary": "100k"}'
        calls = mock_openai_class.return_value.chat.completions.create.call_args_list
        assert len(calls) == 4
        assert [c.kwargs.get("model") for c in calls][:3] == [DEFAULT_MODEL] * 3
        assert calls[3].kwargs.get("model") == DEFAULT_FALLBACK_MODEL

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_fallback_model_used_when_primary_exhausted(self, mock_openai_class):
        mock_openai_class.return_value = make_sequence_choices(
            "garbage not json", "garbage not json", "garbage not json", '{"salary": "100k"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            with patch("aiEnrich.openrouter_client.time.sleep"):
                result = query_openrouter("prompt", fallback_model="nex-agi/nex-n2.5-pro:free")
        assert result == '{"salary": "100k"}'
        calls = mock_openai_class.return_value.chat.completions.create.call_args_list
        assert len(calls) == 4
        assert [c.kwargs.get("model") for c in calls] == [DEFAULT_MODEL, DEFAULT_MODEL, DEFAULT_MODEL, "nex-agi/nex-n2.5-pro:free"]

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_fenced_json_returns_without_fallback(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response('```json\n{"salary": "100k"}\n```')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            result = query_openrouter("prompt", fallback_model="nex-agi/nex-n2.5-pro:free")
        assert result == '```json\n{"salary": "100k"}\n```'
        assert mock_openai_class.return_value.chat.completions.create.call_count == 1

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_succeeds_on_second_retry(self, mock_openai_class):
        mock_openai_class.return_value = make_sequence_choices(Exception("first fail"), '{"key": "value"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            result = query_openrouter("prompt")
        assert result == '{"key": "value"}'
        assert mock_openai_class.return_value.chat.completions.create.call_count == 2

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_split_system_and_user_messages(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response('{"key": "value"}')
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            result = query_openrouter("user prompt here")
        assert result == '{"key": "value"}'
        messages = mock_openai_class.return_value.chat.completions.create.call_args[1]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "user prompt here"

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError):
                query_openrouter("prompt")

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_falls_back_to_openrouter_api_key(self, mock_openai_class):
        mock_openai_class.return_value = make_choice_response('{"key": "value"}')
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-or-fallback"}, clear=True):
            result = query_openrouter("prompt")
        assert result == '{"key": "value"}'
        assert mock_openai_class.call_args[1]["api_key"] == "sk-or-fallback"


class TestPingOpenrouter:

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_success(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            assert ping_openrouter() is True
        mock_openai_class.return_value.models.list.assert_called_once()

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_failure_returns_false(self, mock_openai_class):
        client = MagicMock()
        client.models.list.side_effect = Exception("Connection refused")
        mock_openai_class.return_value = client
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            assert ping_openrouter(timeout=2) is False

    @patch("aiEnrich.openrouter_client.OpenAI")
    def test_uses_custom_base_url_and_timeout(self, mock_openai_class):
        mock_openai_class.return_value = MagicMock()
        with patch.dict("os.environ", {"AI_ENRICH_OPENROUTER_API_KEY": "sk-test"}):
            ping_openrouter(base_url="http://custom:11434", timeout=10)
        assert mock_openai_class.call_args[1]["base_url"] == "http://custom:11434"
        assert mock_openai_class.call_args[1]["timeout"] == 10

    def test_defaults(self):
        assert DEFAULT_BASE_URL == "https://openrouter.ai/api/v1"
        assert DEFAULT_MODEL == "openrouter/free"
        assert DEFAULT_FALLBACK_MODEL == "nex-agi/nex-n2.5-pro:free"