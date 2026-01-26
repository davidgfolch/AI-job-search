import pytest
from unittest.mock import patch, MagicMock

from ..crew import AiJobSearchFlow


class TestAiJobSearchFlow:
    @patch('aiEnrich.crew.CVLoader')
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.cvMatch')
    @patch('aiEnrich.crew.getEnvBool')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows_no_cv_match(self, mock_print_hr, mock_console_timer, 
                                     mock_get_env_bool, mock_cv_match, 
                                     mock_data_extractor, mock_cv_loader_cls):
        mock_get_env_bool.return_value = False
        mock_cv_loader = mock_cv_loader_cls.return_value
        mock_cv_loader.load_cv_content.return_value = True
        mock_data_extractor.side_effect = [1, 0]  # First call returns 1, second returns 0
        
        flow = AiJobSearchFlow()
        
        # Mock the while loop to run only twice
        with patch('builtins.iter', side_effect=[[True, False]]):
            try:
                flow.processRows()
            except StopIteration:
                pass  # Expected when mocking the infinite loop
        
        mock_cv_loader.load_cv_content.assert_called_once()
        assert mock_data_extractor.call_count >= 1

    @patch('aiEnrich.crew.CVLoader')
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.cvMatch')
    @patch('aiEnrich.crew.getEnvBool')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows_with_cv_match(self, mock_print_hr, mock_console_timer,
                                       mock_get_env_bool, mock_cv_match,
                                       mock_data_extractor, mock_cv_loader_cls):
        mock_get_env_bool.return_value = True
        mock_cv_loader = mock_cv_loader_cls.return_value
        mock_cv_loader.load_cv_content.return_value = True
        mock_data_extractor.return_value = 0
        mock_cv_match.side_effect = [1, 0]  # First call returns 1, second returns 0
        
        flow = AiJobSearchFlow()
        
        # Mock the while loop to run only twice
        call_count = 0
        def mock_data_extractor_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count > 2:
                raise StopIteration()
            return 0
        
        mock_data_extractor.side_effect = mock_data_extractor_side_effect
        
        try:
            flow.processRows()
        except StopIteration:
            pass  # Expected when mocking the infinite loop
        
        mock_cv_loader.load_cv_content.assert_called_once()
        mock_cv_match.assert_called()

    @patch('aiEnrich.crew.CVLoader')
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.getEnvBool')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows_cv_not_loaded(self, mock_print_hr, mock_console_timer,
                                       mock_get_env_bool, mock_data_extractor, 
                                       mock_cv_loader_cls):
        mock_get_env_bool.return_value = True
        mock_cv_loader = mock_cv_loader_cls.return_value
        mock_cv_loader.load_cv_content.return_value = False  # CV not loaded
        mock_data_extractor.return_value = 0
        
        flow = AiJobSearchFlow()
        
        # Mock the while loop to run only once
        call_count = 0
        def mock_data_extractor_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise StopIteration()
            return 0
        
        mock_data_extractor.side_effect = mock_data_extractor_side_effect
        
        try:
            flow.processRows()
        except StopIteration:
            pass  # Expected when mocking the infinite loop
        
        mock_cv_loader.load_cv_content.assert_called_once()