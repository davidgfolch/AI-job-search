import unittest
from unittest.mock import MagicMock, patch, mock_open
import numpy as np
from aiEnrichNew.fastCvMatcher import FastCVMatcher

class TestFastCVMatcher(unittest.TestCase):

    @patch('aiEnrichNew.fastCvMatcher.SentenceTransformer')
    def setUp(self, mock_transformer):
        # Reset singleton for testing
        FastCVMatcher._instance = None
        
        # Setup mock model
        self.mock_model = MagicMock()
        mock_transformer.return_value = self.mock_model
        
        self.matcher = FastCVMatcher()

    def test_initialization(self):
        self.assertIsNotNone(self.matcher._model)

    @patch('aiEnrichNew.fastCvMatcher.getEnvBool')
    def test_load_cv_disabled_env(self, mock_get_env):
        mock_get_env.return_value = False
        result = self.matcher._load_cv_content()
        self.assertFalse(result)

    @patch('aiEnrichNew.fastCvMatcher.getEnvBool')
    @patch('aiEnrichNew.fastCvMatcher.Path')
    def test_load_cv_file_not_found(self, mock_path, mock_get_env):
        mock_get_env.return_value = True
        # Mock objects not existing
        mock_path_obj = MagicMock()
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = False
        
        result = self.matcher._load_cv_content()
        self.assertFalse(result)

    @patch('aiEnrichNew.fastCvMatcher.getEnvBool')
    @patch('aiEnrichNew.fastCvMatcher.Path')
    def test_load_cv_txt_success(self, mock_path, mock_get_env):
        mock_get_env.return_value = True
        
        # Setup mocks for file existence
        mock_path_pdf = MagicMock()
        mock_path_txt = MagicMock()
        
        # When Path is called with pdf path, return mock_path_pdf
        # When called with txt path, return mock_path_txt
        # Simplified: We can just check behaviors based on side_effect or checks
        
        # Let's mock the Path behavior specifically
        # The code creates Path(CV_LOCATION) and Path(cvLocationTxt)
        # We can simulate success path: text file exists
        
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

if __name__ == '__main__':
    unittest.main()
