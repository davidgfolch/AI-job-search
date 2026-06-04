import unittest
from ..base import AIProvider, AnswerResult


class TestAnswerResult(unittest.TestCase):
    def test_default_is_not_clarification(self):
        r = AnswerResult(text="some answer")
        self.assertFalse(r.is_clarification)
        self.assertEqual(r.provider, "unknown")

    def test_clarification_flag(self):
        r = AnswerResult(text="CLARIFICACIÓN: need more info", is_clarification=True)
        self.assertTrue(r.is_clarification)

    def test_custom_provider(self):
        r = AnswerResult(text="answer", provider="openai")
        self.assertEqual(r.provider, "openai")


class TestAIProvider(unittest.TestCase):
    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            AIProvider()
