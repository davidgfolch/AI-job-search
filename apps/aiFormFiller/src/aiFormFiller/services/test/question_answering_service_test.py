import unittest
from unittest.mock import MagicMock, patch
from ...test.helpers import TempFiles, make_mock_cfg, make_mock_provider
from ..question_answering_service import QuestionAnsweringService
from ...context_loader import ContextLoader


class TestQuestionAnsweringService(unittest.TestCase):
    def setUp(self):
        self.temp = TempFiles()
        self.loader = ContextLoader(self.temp.cv_path, self.temp.lf_path)
        self.loader.load()
        self.service = QuestionAnsweringService(self.loader)

    def tearDown(self):
        self.temp.cleanup()

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_uses_local_provider(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg, provider="local")
        mock_hf.return_value = make_mock_provider(text="Tengo 5 años de experiencia con Java", provider="local")
        result = self.service.answer("¿Años de Java?", "local")
        self.assertEqual(result.text, "Tengo 5 años de experiencia con Java")
        mock_hf.assert_called_with("Qwen/Qwen2.5-1.5B-Instruct")

    @patch("aiFormFiller.services.question_answering_service.OpenAIProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_uses_openai_provider(self, mock_cfg, mock_openai):
        make_mock_cfg(mock_cfg, provider="openai")
        mock_openai.return_value = make_mock_provider(text="Answer", provider="openai")
        result = self.service.answer("Question?", "openai")
        self.assertEqual(result.text, "Answer")
        mock_openai.assert_called_with("sk-test", "gpt-4o-mini")

    @patch("aiFormFiller.services.question_answering_service.OpenRouterProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_uses_openrouter_provider(self, mock_cfg, mock_or):
        make_mock_cfg(mock_cfg, provider="openrouter")
        mock_or.return_value = make_mock_provider(text="OR Answer", provider="openrouter")
        result = self.service.answer("Question?", "openrouter")
        self.assertEqual(result.text, "OR Answer")

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_builds_prompt_with_context(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider()
        self.service.answer("Question?")
        _, kwargs = mock_hf.return_value.generate.call_args
        self.assertIn("5 years Java", kwargs["system_prompt"])
        self.assertIn("Salary: 80k", kwargs["system_prompt"])

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_system_prompt_includes_inference_rules(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider()
        self.service.answer("¿Años con Java 11+?")
        _, kwargs = mock_hf.return_value.generate.call_args
        sp = kwargs["system_prompt"]
        self.assertIn("INFERIR", sp)
        self.assertIn("PRIMERA PERSONA", sp)

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_follow_up(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider(text="Updated answer")
        result = self.service.follow_up("¿Años de Java?", "Tengo 2 años con Spring Boot 3")
        self.assertEqual(result.text, "Updated answer")

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_follow_up_includes_clarification_in_prompt(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider()
        self.service.follow_up("question", "clarification info")
        _, kwargs = mock_hf.return_value.generate.call_args
        self.assertIn("clarification info", kwargs["user_message"])

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_batch_returns_correct_number(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider()
        results = self.service.answer_batch(["Q1?", "Q2?", "Q3?"])
        self.assertEqual(len(results), 3)
        self.assertEqual(mock_hf.return_value.generate.call_count, 3)

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_batch_reloads_context_once(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider()
        with patch.object(self.service.context_loader, "reload_if_changed") as mock_reload:
            self.service.answer_batch(["Q1?", "Q2?"])
            mock_reload.assert_called_once()

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_batch_passes_each_question(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mock_hf.return_value = make_mock_provider()
        self.service.answer_batch(["Java?", "Salary?"])
        calls = mock_hf.return_value.generate.call_args_list
        self.assertEqual(calls[0].kwargs["user_message"], "Java?")
        self.assertEqual(calls[1].kwargs["user_message"], "Salary?")

    @patch("aiFormFiller.services.question_answering_service.LocalHFProvider")
    @patch("aiFormFiller.services.question_answering_service.cfg")
    def test_answer_batch_mixed_answers(self, mock_cfg, mock_hf):
        make_mock_cfg(mock_cfg)
        mp = MagicMock()
        def side_effect(system_prompt, user_message, **kw):
            if "Java" in user_message:
                return MagicMock(text="5 años", is_clarification=False, provider="local")
            return MagicMock(text="CLARIFICACIÓN: No se encuentra", is_clarification=True, provider="local")
        mp.generate.side_effect = side_effect
        mock_hf.return_value = mp
        results = self.service.answer_batch(["Java?", "Inglés?"])
        self.assertFalse(results[0].is_clarification)
        self.assertEqual(results[0].text, "5 años")
        self.assertTrue(results[1].is_clarification)
