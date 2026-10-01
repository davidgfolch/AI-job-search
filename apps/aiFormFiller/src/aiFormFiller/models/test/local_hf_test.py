import unittest
from unittest.mock import MagicMock, patch
from .. import local_hf
from ..local_hf import LocalHFProvider


class TestGetPipeline(unittest.TestCase):
    def tearDown(self):
        local_hf._PIPELINE = None
        local_hf._MODEL_ID = None

    @patch("aiFormFiller.models.local_hf.logger")
    @patch("aiFormFiller.models.local_hf.pipeline")
    @patch("aiFormFiller.models.local_hf.AutoModelForCausalLM")
    @patch("aiFormFiller.models.local_hf.AutoTokenizer")
    def test_get_pipeline_logs_load_events(self, mock_tokenizer, mock_model, mock_pipeline, mock_logger):
        tokenizer = MagicMock()
        tokenizer.pad_token = "<eos>"
        mock_tokenizer.from_pretrained.return_value = tokenizer
        mock_pipeline.return_value = "pipe"

        with patch.object(local_hf.torch.cuda, "is_available", return_value=False):
            result = local_hf.get_pipeline("Qwen/Qwen2.5-1.5B-Instruct")

        self.assertEqual(result, "pipe")
        mock_logger.info.assert_any_call("model.loading", provider="local", model="Qwen/Qwen2.5-1.5B-Instruct")
        mock_logger.info.assert_any_call("model.loaded", provider="local", model="Qwen/Qwen2.5-1.5B-Instruct")

    @patch("aiFormFiller.models.local_hf.logger")
    @patch("aiFormFiller.models.local_hf.pipeline")
    @patch("aiFormFiller.models.local_hf.AutoModelForCausalLM")
    @patch("aiFormFiller.models.local_hf.AutoTokenizer")
    def test_get_pipeline_reuses_cached_model(self, mock_tokenizer, mock_model, mock_pipeline, mock_logger):
        local_hf._PIPELINE, local_hf._MODEL_ID = "cached", "cached-model"

        with patch.object(local_hf.torch.cuda, "is_available", return_value=False):
            result = local_hf.get_pipeline("cached-model")

        self.assertEqual(result, "cached")
        mock_pipeline.assert_not_called()
        mock_logger.info.assert_not_called()


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
