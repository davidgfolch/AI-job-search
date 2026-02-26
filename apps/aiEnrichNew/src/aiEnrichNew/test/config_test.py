import unittest
from unittest.mock import patch
from ..config import (
    get_job_system_prompt,
    get_skill_system_prompt,
    get_batch_size,
    get_input_max_len,
    get_enrich_timeout_job,
    get_enrich_timeout_skill,
    should_cleanup_gpu
)

class TestConfig(unittest.TestCase):

    def test_get_job_system_prompt(self):
        prompt = get_job_system_prompt()
        self.assertIn("You are an expert at analyzing job offers", prompt)
        self.assertIn("required_technologies", prompt)

    @patch("aiEnrichNew.config.getEnv")
    def test_get_skill_system_prompt(self, mock_get_env):
        mock_get_env.return_value = "Language, Framework"
        prompt = get_skill_system_prompt()
        self.assertIn("Language, Framework", prompt)
        mock_get_env.assert_called_with("AI_ENRICHNEW_SKILL_CATEGORIES", required=True)

    @patch("aiEnrichNew.config.getEnv")
    def test_get_batch_size_default(self, mock_get_env):
        mock_get_env.return_value = "10"
        self.assertEqual(get_batch_size(), 10)
        mock_get_env.assert_called_with("AI_ENRICHNEW_BATCH_SIZE", "10")

    @patch("aiEnrichNew.config.getEnv")
    def test_get_batch_size_custom(self, mock_get_env):
        mock_get_env.return_value = "50"
        self.assertEqual(get_batch_size(), 50)

    @patch("aiEnrichNew.config.getEnv")
    def test_get_input_max_len(self, mock_get_env):
        mock_get_env.return_value = "5000"
        self.assertEqual(get_input_max_len(), 5000)

    @patch("aiEnrichNew.config.getEnv")
    def test_get_enrich_timeout_job(self, mock_get_env):
        mock_get_env.return_value = "120.5"
        self.assertEqual(get_enrich_timeout_job(), 120.5)

    @patch("aiEnrichNew.config.getEnv")
    def test_get_enrich_timeout_skill(self, mock_get_env):
        mock_get_env.return_value = "60"
        self.assertEqual(get_enrich_timeout_skill(), 60.0)

    @patch("aiEnrichNew.config.getEnv")
    def test_should_cleanup_gpu_true(self, mock_get_env):
        mock_get_env.return_value = "True"
        self.assertTrue(should_cleanup_gpu())

    @patch("aiEnrichNew.config.getEnv")
    def test_should_cleanup_gpu_false(self, mock_get_env):
        mock_get_env.return_value = "False"
        self.assertFalse(should_cleanup_gpu())
