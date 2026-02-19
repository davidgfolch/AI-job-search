import unittest
from unittest.mock import patch
from ..mappers import map_db_job_to_domain, build_job_prompt_messages, build_skill_prompt_messages

class TestMappers(unittest.TestCase):

    @patch("aiEnrichNew.domain.mappers.mapJob")
    def test_map_db_job_to_domain(self, mock_mapJob):
        mock_mapJob.return_value = ("Title", "Company", "Markdown content")
        job_row = (1, "other", "data")
        
        result = map_db_job_to_domain(job_row)
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['title'], "Title")
        self.assertEqual(result['company'], "Company")
        self.assertEqual(result['markdown'], "Markdown content")
        self.assertEqual(result['length'], 16)
        mock_mapJob.assert_called_with(job_row)

    @patch("aiEnrichNew.domain.mappers.get_job_system_prompt")
    @patch("aiEnrichNew.domain.mappers.get_input_max_len")
    def test_build_job_prompt_messages(self, mock_max_len, mock_sys_prompt):
        mock_max_len.return_value = 100
        mock_sys_prompt.return_value = "System Prompt"
        
        job = {
            'title': "Job Title",
            'markdown': "A" * 50
        }
        
        messages = build_job_prompt_messages(job)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[0]['content'], "System Prompt")
        self.assertEqual(messages[1]['role'], 'user')
        self.assertIn("Job Title", messages[1]['content'])
        self.assertIn("A" * 50, messages[1]['content'])

    @patch("aiEnrichNew.domain.mappers.get_job_system_prompt")
    @patch("aiEnrichNew.domain.mappers.get_input_max_len")
    def test_build_job_prompt_messages_truncated(self, mock_max_len, mock_sys_prompt):
        mock_max_len.return_value = 10
        mock_sys_prompt.return_value = "System Prompt"
        
        job = {
            'title': "Job Title",
            'markdown': "A" * 20
        }
        
        messages = build_job_prompt_messages(job)
        
        self.assertIn("...(truncated)", messages[1]['content'])
        self.assertFalse("A" * 20 in messages[1]['content'])

    @patch("aiEnrichNew.domain.mappers.get_skill_system_prompt")
    def test_build_skill_prompt_messages(self, mock_sys_prompt):
        mock_sys_prompt.return_value = "Skill System Prompt"
        skill_name = "Python"
        context = "Used in data science"
        
        messages = build_skill_prompt_messages(skill_name, context)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[0]['content'], "Skill System Prompt")
        self.assertEqual(messages[1]['role'], 'user')
        self.assertIn("Skill: Python", messages[1]['content'])
        self.assertIn("Context (related technologies found in jobs): Used in data science", messages[1]['content'])
