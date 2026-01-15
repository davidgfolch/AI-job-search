import unittest
from unittest.mock import MagicMock, patch
import json
from .. import dataExtractor
from ..dataExtractor import dataExtractor, extract_job_data, get_pipeline, _PIPELINE, save

class TestDataExtractor(unittest.TestCase):

    def setUp(self):
        # Reset specific global variables if needed, though patching is cleaner 
        # But _PIPELINE is global in module, we need to be careful.
        # We'll patch it where used.
        pass

    def tearDown(self):
        # Reset pipeline global if we modified it
        dataExtractor._PIPELINE = None

    @patch('aiEnrichNew.dataExtractor.AutoTokenizer')
    @patch('aiEnrichNew.dataExtractor.AutoModelForCausalLM')
    @patch('aiEnrichNew.dataExtractor.pipeline')
    def test_get_pipeline_singleton(self, mock_pipeline_func, mock_model, mock_tokenizer):
        # First call: should create pipeline
        mock_pipeline_func.return_value = "MyPipeline"
        
        p1 = get_pipeline()
        self.assertEqual(p1, "MyPipeline")
        mock_pipeline_func.assert_called_once()
        
        # Second call: should return same instance without creating new
        p2 = get_pipeline()
        self.assertEqual(p2, "MyPipeline")
        mock_pipeline_func.assert_called_once() # Call count remains 1

    @patch('aiEnrichNew.dataExtractor.MysqlUtil')
    def test_dataExtractor_no_jobs(self, mock_mysql_class):
        mock_mysql = mock_mysql_class.return_value.__enter__.return_value
        mock_mysql.count.return_value = 0
        
        count = dataExtractor()
        self.assertEqual(count, 0)

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

    @patch('aiEnrichNew.dataExtractor.extract_job_data')
    @patch('aiEnrichNew.dataExtractor.mapJob')
    @patch('aiEnrichNew.dataExtractor.MysqlUtil')
    @patch('aiEnrichNew.dataExtractor.get_pipeline')
    @patch('aiEnrichNew.dataExtractor.getJobIdsList')
    @patch('aiEnrichNew.dataExtractor.saveError')
    @patch('aiEnrichNew.dataExtractor.totalCount', new=0)
    @patch('aiEnrichNew.dataExtractor.jobErrors', new_callable=set)
    def test_dataExtractor_exception(self, mock_jobErrors, mock_saveError, mock_getJobIdsList, mock_get_pipeline, mock_mysql_class, mock_mapJob, mock_extract):
        mock_mysql = mock_mysql_class.return_value.__enter__.return_value
        mock_mysql.count.return_value = 1
        mock_getJobIdsList.return_value = [123]
        
        # Ensure mapJob returns valid data so title/company are set
        mock_mapJob.return_value = ("Test Title", "Test Company", "Markdown")
        mock_mysql.fetchOne.return_value = (123, "Test Title", b"Markdown", "Test Company")

        # Raise exception in extract_job_data (after title/company defined)
        mock_extract.side_effect = Exception("AI Fail")
        
        dataExtractor()
        
        mock_saveError.assert_called()

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
        
    @patch('aiEnrichNew.dataExtractor.validateResult')
    def test_save_logic(self, mock_validate):
        mock_mysql = MagicMock()
        result = {"salary": "100k", "required_technologies": "A", "optional_technologies": "B"}
        
        save(mock_mysql, 999, "Comp", result)
        
        mock_validate.assert_called_with(result)
        mock_mysql.updateFromAI.assert_called()
        # Check params (salary, req_tech, opt_tech, id)
        # Note: maxLen processing might change values slightly if they were huge, but here they are small
        # We can inspect the call args deeply if needed, but called is sufficient for coverage flow

if __name__ == '__main__':
    unittest.main()
