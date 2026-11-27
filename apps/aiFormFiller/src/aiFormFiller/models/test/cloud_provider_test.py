from unittest.mock import MagicMock, patch

import pytest

from ..cloud_provider import CloudProvider


def _client_with_answer(answer, content_key="content"):
    client = MagicMock()
    message = MagicMock()
    message.content = None if content_key == "reasoning" else answer
    message.reasoning = answer if content_key == "reasoning" else None
    client.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=message)])
    return client


@pytest.mark.parametrize("provider", ["gemini", "groq", "cerebras", "hf-inference"])
@patch("aiFormFiller.models.cloud_provider.OpenAI")
def test_generate_uses_provider_base_url(mock_openai, provider):
    mock_openai.return_value = _client_with_answer("answer")
    result = CloudProvider(provider, "key", "model").generate("system", "question?", 30, 512, 0.1)
    assert result.text == "answer"
    assert result.provider == provider
    assert mock_openai.call_args.kwargs["api_key"] == "key"
    assert mock_openai.call_args.kwargs["base_url"].startswith("https://")


@patch("aiFormFiller.models.cloud_provider.OpenAI")
def test_generate_detects_clarification(mock_openai):
    mock_openai.return_value = _client_with_answer("CLARIFICATION: Missing data")
    assert CloudProvider("groq", "key", "model").generate("system", "question?", 30, 512, 0.1).is_clarification is True


@patch("aiFormFiller.models.cloud_provider.OpenAI")
def test_free_model_disables_reasoning_and_falls_back_to_reasoning_text(mock_openai):
    mock_openai.return_value = _client_with_answer("from reasoning", content_key="reasoning")
    provider = CloudProvider("openrouter", "key", "vendor/model:free")
    assert provider.generate("system", "question?", 30, 512, 0.1).text == "from reasoning"
    assert mock_openai.return_value.chat.completions.create.call_args.kwargs["extra_body"] == {"reasoning": {"enabled": False}}


@patch("aiFormFiller.models.cloud_provider.OpenAI")
def test_paid_model_does_not_send_reasoning_option(mock_openai):
    mock_openai.return_value = _client_with_answer("answer")
    CloudProvider("groq", "key", "model").generate("system", "question?", 30, 512, 0.1)
    assert "extra_body" not in mock_openai.return_value.chat.completions.create.call_args.kwargs
