
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
    @patch('aiEnrich.crew.dataExtractor')
    @patch('aiEnrich.crew.consoleTimer')
    @patch('aiEnrich.crew.printHR')
    def test_process_rows(self, mock_print_hr, mock_console_timer, 
                         mock_data_extractor, mock_skill_enricher, 
                         mock_retry_failed_jobs, mock_ai_job_search_flow):
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
        assert mock_data_extractor.call_count == 3