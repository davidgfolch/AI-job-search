from unittest.mock import MagicMock, patch

import pytest

from commonlib.cloud_llm import (
    CEREBRAS, GEMINI, GROQ, HF_INFERENCE, OPENROUTER, PROVIDERS,
    chat, get_api_key, get_base_url, get_model, is_cloud, ping,
)


@pytest.mark.parametrize("provider", [OPENROUTER, GEMINI, GROQ, CEREBRAS, HF_INFERENCE])
def test_registry_covers_every_provider(provider):
    assert is_cloud(provider)
    spec = PROVIDERS[provider]
    assert spec.base_url.startswith("https://")
    assert spec.api_key_env.endswith("_KEY") or spec.api_key_env == "HF_TOKEN"
    assert spec.default_model


@pytest.mark.parametrize("provider", ["ollama", "huggingface", "local", ""])
def test_local_backends_are_not_cloud(provider):
    assert not is_cloud(provider)


@pytest.mark.parametrize("provider,expected", [
    (GEMINI, "GEMINI_API_KEY"), (GROQ, "GROQ_API_KEY"),
    (CEREBRAS, "CEREBRAS_API_KEY"), (HF_INFERENCE, "HF_TOKEN"),
])
def test_get_api_key_reads_provider_secret(provider, expected):
    with patch("commonlib.cloud_llm.getEnvFile", return_value="secret") as read:
        assert get_api_key(provider) == "secret"
    read.assert_called_once_with(expected, "")


def test_get_api_key_rejects_missing_secret():
    with patch("commonlib.cloud_llm.getEnvFile", return_value=""):
        with pytest.raises(ValueError, match="GROQ_API_KEY is not set"):
            get_api_key(GROQ)


def test_base_url_and_model_honor_env_overrides():
    values = {f"{GROQ.upper()}_MODEL": "custom/model", "GROQ_BASE_URL": "http://local/v1"}
    with patch("commonlib.cloud_llm.getEnvFile", side_effect=lambda key, default: values.get(key, default)):
        assert get_model(GROQ) == "custom/model"
        assert get_base_url(GROQ) == "http://local/v1"


def test_ping_uses_models_endpoint_with_bearer_key():
    response = MagicMock()
    with patch("commonlib.cloud_llm.requests.get", return_value=response) as get, \
         patch("commonlib.cloud_llm.get_api_key", return_value="key"):
        assert ping(GEMINI) is True
    get.assert_called_once()
    assert get.call_args.args[0].endswith("/models")
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer key"}


def test_ping_honors_timeout_and_base_url_overrides():
    with patch("commonlib.cloud_llm.requests.get", return_value=MagicMock()) as get, \
         patch("commonlib.cloud_llm.get_api_key", return_value="key"):
        assert ping(GROQ, timeout=2, base_url="http://local/v1/") is True
    assert get.call_args.args[0] == "http://local/v1/models"
    assert get.call_args.kwargs["timeout"] == 2


def test_ping_returns_false_on_error():
    with patch("commonlib.cloud_llm.requests.get", side_effect=OSError("offline")):
        assert ping(GROQ) is False


def _response(content):
    response = MagicMock()
    response.json.return_value = {"choices": [{"message": {"content": content}}]}
    return response


def test_chat_returns_first_answer_and_disables_free_reasoning():
    with patch("commonlib.cloud_llm.get_api_key", return_value="key"), \
         patch("commonlib.cloud_llm.requests.post", return_value=_response(" answer ")) as post:
        assert chat(OPENROUTER, [{"role": "user", "content": "hi"}]) == "answer"
    assert post.call_args.kwargs["json"]["reasoning"] == {"enabled": False}


def test_chat_adds_json_mode_for_non_free_provider():
    with patch("commonlib.cloud_llm.get_api_key", return_value="key"), \
         patch("commonlib.cloud_llm.requests.post", return_value=_response("{}")) as post:
        chat(GROQ, [{"role": "user", "content": "hi"}], json_mode=True)
    assert post.call_args.kwargs["json"]["response_format"] == {"type": "json_object"}


def test_chat_retries_then_uses_fallback_model():
    failed = MagicMock()
    failed.raise_for_status.side_effect = OSError("boom")
    with patch("commonlib.cloud_llm.get_api_key", return_value="key"), \
         patch("commonlib.cloud_llm.requests.post", side_effect=[failed, failed, failed, _response("from fallback")]) as post, \
         patch("commonlib.cloud_llm.time.sleep"):
        assert chat(OPENROUTER, [{"role": "user", "content": "hi"}]) == "from fallback"
    assert post.call_count == 4
    assert post.call_args.kwargs["json"]["model"] == PROVIDERS[OPENROUTER].fallback_model


def test_chat_returns_none_when_every_attempt_fails():
    with patch("commonlib.cloud_llm.get_api_key", return_value="key"), \
         patch("commonlib.cloud_llm.requests.post", side_effect=OSError("offline")), \
         patch("commonlib.cloud_llm.time.sleep"):
        assert chat(GEMINI, [{"role": "user", "content": "hi"}]) is None
