import unittest
from unittest.mock import MagicMock, patch
from ..local_hf import LocalHFProvider


class TestLocalHFProvider(unittest.TestCase):
    @patch("aiFormFiller.models.local_hf.get_pipeline")
    def test_generate_returns_answer(self, mock_get_pipeline):
        mock_pipe = MagicMock()
        mock_pipe.tokenizer.apply_chat_template.return_value = "<|im_start|>prompt"
        mock_pipe.return_value = [{"generated_text": "Tengo 5 años de experiencia"}]
        mock_get_pipeline.return_value = mock_pipe

        provider = LocalHFProvider("Qwen/Qwen2.5-1.5B-Instruct")
        result = provider.generate("system prompt", "user question", 30, 512, 0.1)

        self.assertEqual(result.text, "Tengo 5 años de experiencia")
        self.assertFalse(result.is_clarification)
        self.assertEqual(result.provider, "local")

    @patch("aiFormFiller.models.local_hf.get_pipeline")
    def test_generate_detects_clarification(self, mock_get_pipeline):
        mock_pipe = MagicMock()
        mock_pipe.tokenizer.apply_chat_template.return_value = "<|im_start|>prompt"
        mock_pipe.return_value = [{"generated_text": "CLARIFICACIÓN: No tengo suficiente info"}]
        mock_get_pipeline.return_value = mock_pipe

        provider = LocalHFProvider("Qwen/Qwen2.5-1.5B-Instruct")
        result = provider.generate("system", "question?", 30, 512, 0.1)
        self.assertTrue(result.is_clarification)

    @patch("aiFormFiller.models.local_hf.get_pipeline")
    def test_generate_builds_messages_correctly(self, mock_get_pipeline):
        mock_pipe = MagicMock()
        mock_pipe.tokenizer.apply_chat_template.return_value = "<|im_start|>prompt"
        mock_pipe.return_value = [{"generated_text": "answer"}]
        mock_get_pipeline.return_value = mock_pipe

        provider = LocalHFProvider("Qwen/Qwen2.5-1.5B-Instruct")
        provider.generate("system msg", "user msg", 30, 512, 0.1)

        mock_pipe.tokenizer.apply_chat_template.assert_called_once()
        args = mock_pipe.tokenizer.apply_chat_template.call_args[0][0]
        self.assertEqual(args[0]["role"], "system")
        self.assertEqual(args[0]["content"], "system msg")
        self.assertEqual(args[1]["role"], "user")
        self.assertEqual(args[1]["content"], "user msg")
