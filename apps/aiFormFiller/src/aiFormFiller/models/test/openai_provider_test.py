import unittest
from unittest.mock import MagicMock, patch


class TestOpenAIProvider(unittest.TestCase):
    @patch("aiFormFiller.models.openai_provider.OpenAI")
    def test_generate_returns_answer(self, mock_openai_class):
        from ..openai_provider import OpenAIProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "Tengo 5 años de experiencia"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        result = provider.generate("system", "question?", 30, 512, 0.1)
        self.assertEqual(result.text, "Tengo 5 años de experiencia")
        self.assertFalse(result.is_clarification)
        self.assertEqual(result.provider, "openai")

    @patch("aiFormFiller.models.openai_provider.OpenAI")
    def test_generate_detects_clarification(self, mock_openai_class):
        from ..openai_provider import OpenAIProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "CLARIFICACIÓN: No se encuentra experiencia con Java 11"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        result = provider.generate("system", "question?", 30, 512, 0.1)
        self.assertTrue(result.is_clarification)

    @patch("aiFormFiller.models.openai_provider.OpenAI")
    def test_generate_uses_correct_model(self, mock_openai_class):
        from ..openai_provider import OpenAIProvider
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "answer"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        provider.generate("system", "question?", 30, 512, 0.1)
        mock_client.chat.completions.create.assert_called_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "question?"},
            ],
            max_tokens=512,
            temperature=0.1,
            timeout=30,
        )
