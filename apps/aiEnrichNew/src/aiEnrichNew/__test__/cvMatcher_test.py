import unittest
from unittest.mock import MagicMock, patch, mock_open
import numpy as np
import pandas as pd
from ..cvMatcher import FastCVMatcher

class TestFastCVMatcher(unittest.TestCase):

    @patch('aiEnrichNew.cvMatcher.SentenceTransformer')
    def setUp(self, mock_transformer):
        # Reset singleton for testing
        FastCVMatcher._instance = None
        
        # Setup mock model
        self.mock_model = MagicMock()
        mock_transformer.return_value = self.mock_model
        
        self.matcher = FastCVMatcher()

    def test_initialization(self):
        self.assertIsNotNone(self.matcher._model)

    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    def test_load_cv_disabled_env(self, mock_get_env):
        mock_get_env.return_value = False
        result = self.matcher._load_cv_content()
        self.assertFalse(result)

    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    @patch('aiEnrichNew.cvMatcher.Path')
    def test_load_cv_file_not_found(self, mock_path, mock_get_env):
        mock_get_env.return_value = True
        # Mock objects not existing
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = False
        
        result = self.matcher._load_cv_content()
        self.assertFalse(result)

    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    @patch('aiEnrichNew.cvMatcher.Path')
    def test_load_cv_txt_success(self, mock_path, mock_get_env):
        mock_get_env.return_value = True
        
        def path_side_effect(arg):
            m = MagicMock()
            if arg.endswith('.txt'):
                m.exists.return_value = True
            else:
                m.exists.return_value = False
            return m
            
        mock_path.side_effect = path_side_effect

        with patch('builtins.open', mock_open(read_data="My Resume Content")):
            # Mock encode return
            self.mock_model.encode.return_value = np.array([[1.0, 0.0]])
            
            result = self.matcher._load_cv_content()
            
            self.assertTrue(result)
            self.assertIsNotNone(self.matcher._cv_embedding)
            self.assertEqual(self.matcher._cv_content, "My Resume Content")

    def test_match_no_cv(self):
        # Ensure no CV is loaded
        self.matcher._cv_embedding = None
        result = self.matcher.match("Job Description")
        self.assertEqual(result, {"cv_match_percentage": 0})

    def test_match_success(self):
        # Setup CV embedding (mocking directly for simplicity)
        self.matcher._cv_embedding = np.array([[1.0, 0.0]])
        
        # Mock job embedding
        self.mock_model.encode.return_value = np.array([[0.0, 1.0]])
        
        # Cosine similarity of orthogonal vectors is 0
        result = self.matcher.match("Job Description")
        self.assertEqual(result, {"cv_match_percentage": 0})

        # Mock job embedding same as CV
        self.mock_model.encode.return_value = np.array([[1.0, 0.0]])
        # Cosine similarity should be 1 -> 100%
        result = self.matcher.match("Job Description")
        self.assertEqual(result, {"cv_match_percentage": 100})
    
    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    def test_process_db_jobs_cv_disabled(self, mock_getEnvBool):
        mock_getEnvBool.return_value = False
        result = self.matcher.process_db_jobs()
        self.assertEqual(result, 0)
        
    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    def test_process_db_jobs_cv_load_fail(self, mock_getEnvBool):
        mock_getEnvBool.return_value = True
        # _load_cv_content fails (returns False) by default if not mocked/setup
        with patch.object(self.matcher, '_load_cv_content', return_value=False):
            result = self.matcher.process_db_jobs()
            self.assertEqual(result, 0)

    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    @patch('aiEnrichNew.cvMatcher.MysqlUtil')
    def test_process_db_jobs_count_zero(self, mock_mysql_class, mock_getEnvBool):
        mock_getEnvBool.return_value = True
        with patch.object(self.matcher, '_load_cv_content', return_value=True):
            mock_mysql = mock_mysql_class.return_value.__enter__.return_value
            mock_mysql.count.return_value = 0
            
            result = self.matcher.process_db_jobs()
            self.assertEqual(result, 0)

    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    @patch('aiEnrichNew.cvMatcher.MysqlUtil')
    def test_process_db_jobs_flow(self, mock_mysql_class, mock_getEnvBool):
        mock_getEnvBool.return_value = True
        with patch.object(self.matcher, '_load_cv_content', return_value=True):
            mock_mysql = mock_mysql_class.return_value.__enter__.return_value
            mock_mysql.count.return_value = 1
            mock_mysql.fetchAll.return_value = [(101,)] # IDs
            # Mock fetchOne returning job details
            mock_mysql.fetchOne.return_value = (101, "Dev Job", b"Markdown desc", "Tech Corp")
            
            with patch.object(self.matcher, 'match', return_value={'cv_match_percentage': 85}):
                 result = self.matcher.process_db_jobs()
                 self.assertEqual(result, 1)
                 # Verify save
                 mock_mysql.updateFromAI.assert_called()

    @patch('aiEnrichNew.cvMatcher.getEnvBool')
    @patch('aiEnrichNew.cvMatcher.MysqlUtil')
    def test_process_db_jobs_exception(self, mock_mysql_class, mock_getEnvBool):
        mock_getEnvBool.return_value = True
        with patch.object(self.matcher, '_load_cv_content', return_value=True):
            mock_mysql = mock_mysql_class.return_value.__enter__.return_value
            mock_mysql.count.return_value = 1
            mock_mysql.fetchAll.return_value = [(101,)] 
            mock_mysql.fetchOne.return_value = (101, "Dev Job", b"Markdown desc", "Tech Corp")
            
            # Raise exception during match (after fetchOne)
            with patch.object(self.matcher, 'match', side_effect=Exception("DB Error")):
                result = self.matcher.process_db_jobs()
            
            # Should catch exception and save error
            mock_mysql.updateFromAI.assert_not_called()
            # updateFieldsQuery is called in _save_error
            mock_mysql.executeAndCommit.assert_called() 
            self.assertEqual(len(self.matcher.jobErrors), 1)

    @patch('aiEnrichNew.cvMatcher.pdfplumber')
    def test_extract_text_from_pdf(self, mock_pdfplumber):
        mock_pdf = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        mock_page = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_page.extract_text.return_value = "Page text"
        # Mock table extraction
        mock_page.extract_tables.return_value = [[["Col1", "Col2"], ["Val1", "Val2"]]]
        
        # Mock df.to_markdown to avoid tabulate dependency
        with patch('pandas.DataFrame.to_markdown', return_value="| Col1 | Col2 |\n|---|---|\n| Val1 | Val2 |"):
            text = self.matcher._extract_text_from_pdf("dummy.pdf")
        
        self.assertIn("Page text", text)
        self.assertIn("Val1", text) 
        self.assertIn("Val2", text)

    def test_match_exception(self):
        self.matcher._cv_embedding = np.array([[1.0]])
        # Mock model to raise exception
        self.mock_model.encode.side_effect = Exception("Encode fail")
        
        result = self.matcher.match("Desc")
        self.assertEqual(result, {"cv_match_percentage": 0})

if __name__ == '__main__':
    unittest.main()
