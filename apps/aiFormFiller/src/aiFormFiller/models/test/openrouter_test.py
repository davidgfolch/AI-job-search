import unittest
from unittest.mock import MagicMock, patch
from ..openrouter import OPENROUTER_BASE_URL


class TestOpenRouterProvider(unittest.TestCase):
    @patch("aiFormFiller.models.openrouter.OpenAI")
    def test_generate_returns_answer(self, mock_openai_class):
        from ..openrouter import OpenRouterProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "Tengo 3 años de experiencia"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenRouterProvider(api_key="test-key", model="openai/gpt-4o-mini")
        result = provider.generate("system", "question?", 30, 512, 0.1)
        self.assertEqual(result.text, "Tengo 3 años de experiencia")
        self.assertFalse(result.is_clarification)
        self.assertEqual(result.provider, "openrouter")

    @patch("aiFormFiller.models.openrouter.OpenAI")
    def test_generate_uses_correct_base_url(self, mock_openai_class):
        from ..openrouter import OpenRouterProvider
        OpenRouterProvider(api_key="key", model="model")
        mock_openai_class.assert_called_with(base_url=OPENROUTER_BASE_URL, api_key="key")

    @patch("aiFormFiller.models.openrouter.OpenAI")
    def test_generate_detects_clarification(self, mock_openai_class):
        from ..openrouter import OpenRouterProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "CLARIFICATION: Missing data"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenRouterProvider(api_key="test-key", model="openai/gpt-4o-mini")
        result = provider.generate("system", "question?", 30, 512, 0.1)
        self.assertTrue(result.is_clarification)

    @patch("aiFormFiller.models.openrouter.OpenAI")
    def test_free_model_disables_reasoning(self, mock_openai_class):
        from ..openrouter import OpenRouterProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "Tengo 5 años de experiencia"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenRouterProvider(api_key="key", model="nvidia/nemotron-3.5-lightning:free")
        result = provider.generate("system", "question?", 30, 512, 0.1)
        self.assertEqual(result.text, "Tengo 5 años de experiencia")
        mock_client.chat.completions.create.assert_called_once_with(
            model="nvidia/nemotron-3.5-lightning:free",
            messages=[{"role": "system", "content": "system"}, {"role": "user", "content": "question?"}],
            max_tokens=512, temperature=0.1, timeout=30,
            extra_body={"reasoning": {"enabled": False}},
        )

    @patch("aiFormFiller.models.openrouter.OpenAI")
    def test_null_content_falls_back_to_reasoning(self, mock_openai_class):
        from ..openrouter import OpenRouterProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = None
        mock_choice.message.reasoning = "Tengo 5 años de experiencia"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenRouterProvider(api_key="key", model="nvidia/nemotron-3.5-lightning:free")
        self.assertEqual(provider.generate("system", "question?", 30, 512, 0.1).text, "Tengo 5 años de experiencia")
