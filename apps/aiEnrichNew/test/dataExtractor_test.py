import unittest
from unittest.mock import MagicMock, patch
import json
from aiEnrichNew.dataExtractor import dataExtractor, extract_job_data

class TestDataExtractor(unittest.TestCase):

    @patch('aiEnrichNew.dataExtractor.MysqlUtil')
    @patch('aiEnrichNew.dataExtractor.get_pipeline')
    @patch('aiEnrichNew.dataExtractor.getJobIdsList')
    @patch('aiEnrichNew.dataExtractor.save')
    @patch('aiEnrichNew.dataExtractor.mapJob')
    def test_dataExtractor_flow(self, mock_mapJob, mock_save, mock_getJobIdsList, mock_get_pipeline, mock_mysql_class):
        # Setup mocks
        mock_mysql = mock_mysql_class.return_value.__enter__.return_value
        mock_mysql.count.return_value = 1
        mock_getJobIdsList.return_value = [123]
        mock_mysql.fetchOne.return_value = ("id", "Title", "Markdown", "Company")
        mock_mapJob.return_value = ("Title", "Company", "Markdown")
        
        # Mock pipeline
        mock_pipe = MagicMock()
        mock_get_pipeline.return_value = mock_pipe
        
        # Mock LLM generation result
        mock_pipe.tokenizer.apply_chat_template.return_value = "prompt"
        mock_pipe.return_value = [{'generated_text': '{"salary": "50k"}'}]

        # Run
        added_count = dataExtractor()

        # Verify
        self.assertEqual(added_count, 1)
        mock_save.assert_called_once()
        args, _ = mock_save.call_args
        self.assertEqual(args[1], 123) # id
        self.assertEqual(args[3], {"salary": "50k"}) # result

    def test_extract_job_data(self):
        mock_pipe = MagicMock()
        mock_pipe.tokenizer.apply_chat_template.return_value = "prompt"
        expected_json = {
            "required_technologies": "python",
            "optional_technologies": "docker",
            "salary": "100k"
        }
        mock_pipe.return_value = [{'generated_text': json.dumps(expected_json)}]
        
        result = extract_job_data(mock_pipe, "Job Title", "Job Description")
        
        self.assertEqual(result, expected_json)
        mock_pipe.assert_called_once()

if __name__ == '__main__':
    unittest.main()
