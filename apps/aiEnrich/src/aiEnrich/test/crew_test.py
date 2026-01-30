
import pytest
from unittest.mock import patch, MagicMock
import sys
import importlib

@pytest.fixture
def mock_ai_job_search_flow():
    # Define mocks with __spec__ = None to satisfy importlib
    mock_flow_module = MagicMock()
    mock_flow_module.Flow = MagicMock
    mock_flow_module.start = lambda: lambda x: x
    mock_flow_module.__spec__ = None

    mock_crewai = MagicMock()
    mock_crewai.__path__ = []
    mock_crewai.__spec__ = None

    mock_project = MagicMock()
    mock_project.__spec__ = None

    mock_crews = MagicMock()
    mock_crews.__spec__ = None

    mock_crew_output = MagicMock()
    mock_crew_output.__spec__ = None

    # Patch sys.modules
    modules_to_patch = {
        'crewai.flow.flow': mock_flow_module,
        'crewai': mock_crewai,
        'crewai.project': mock_project,
        'crewai.crews': mock_crews,
        'crewai.crews.crew_output': mock_crew_output
    }
    # Backup original aiEnrich modules
    original_modules = {k: v for k, v in sys.modules.items() if k.startswith('aiEnrich')}
    
    with patch.dict(sys.modules, modules_to_patch):
        # Force re-import of aiEnrich modules using mocks
        # We only need to pop the ones that import crewai, mainly aiEnrich.crew
        # But safest to pop all aiEnrich to avoid mismatch
        for key in list(sys.modules.keys()):
            if key.startswith('aiEnrich'):
                sys.modules.pop(key, None)
        
        # Now import the module under test
        from ..crew import AiJobSearchFlow
        yield AiJobSearchFlow
        
    # Restore original modules
    # First clear out the mocked versions
    for key in list(sys.modules.keys()):
        if key.startswith('aiEnrich'):
            sys.modules.pop(key, None)
    
    # Then put back the originals
    sys.modules.update(original_modules)

class TestAiJobSearchFlow:
    @patch('aiEnrich.crew.retry_failed_jobs')
    @patch('aiEnrich.crew.skillEnricher')
    @patch('aiEnrich.crew.CVLoader')
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.cvMatch')
    @patch('aiEnrich.crew.getEnvBool')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows_no_cv_match(self, mock_print_hr, mock_console_timer, 
                                     mock_get_env_bool, mock_cv_match, 
                                     mock_data_extractor, mock_cv_loader_cls,
                                     mock_skill_enricher, mock_retry_failed_jobs,
                                     mock_ai_job_search_flow):
        mock_get_env_bool.return_value = False
        mock_cv_loader = mock_cv_loader_cls.return_value
        mock_cv_loader.load_cv_content.return_value = True
        # side_effect=[1, 0] ensures that:
        # 1. First call returns 1 -> loop continues
        # 2. Second call returns 0 -> enters if block
        # 3. Third call raises StopIteration (iterator exhausted) -> breaks loop
        mock_data_extractor.side_effect = [1, 0]
        mock_skill_enricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        flow = mock_ai_job_search_flow()
        try:
            flow.processRows()
        except StopIteration:
            pass  # Expected when mocking the infinite loop
        mock_cv_loader.load_cv_content.assert_called_once()
        assert mock_data_extractor.call_count == 3

    @patch('aiEnrich.crew.retry_failed_jobs')
    @patch('aiEnrich.crew.skillEnricher')
    @patch('aiEnrich.crew.CVLoader')
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.cvMatch')
    @patch('aiEnrich.crew.getEnvBool')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows_with_cv_match(self, mock_print_hr, mock_console_timer,
                                       mock_get_env_bool, mock_cv_match,
                                       mock_data_extractor, mock_cv_loader_cls, 
                                       mock_skill_enricher, mock_retry_failed_jobs,
                                       mock_ai_job_search_flow):
        mock_get_env_bool.return_value = True
        mock_cv_loader = mock_cv_loader_cls.return_value
        mock_cv_loader.load_cv_content.return_value = True
        mock_skill_enricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        mock_data_extractor.return_value = 0
        mock_cv_match.side_effect = [1, 0]  # First call returns 1, second returns 0
        flow = mock_ai_job_search_flow()
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

    @patch('aiEnrich.crew.retry_failed_jobs')
    @patch('aiEnrich.crew.skillEnricher')
    @patch('aiEnrich.crew.CVLoader')
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.getEnvBool')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows_cv_not_loaded(self, mock_print_hr, mock_console_timer,
                                       mock_get_env_bool, mock_data_extractor, 
                                       mock_cv_loader_cls, 
                                       mock_skill_enricher, mock_retry_failed_jobs,
                                       mock_ai_job_search_flow):
        mock_get_env_bool.return_value = True
        mock_cv_loader = mock_cv_loader_cls.return_value
        mock_cv_loader.load_cv_content.return_value = False  # CV not loaded
        mock_data_extractor.return_value = 0
        mock_skill_enricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        flow = mock_ai_job_search_flow()
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