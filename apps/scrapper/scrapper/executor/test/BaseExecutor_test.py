import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import CLOSE_TAB, SCRAPPERS, TIMER
from scrapper.executor.BaseExecutor import BaseExecutor

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    return {'sel': sel, 'pm': pm}

@pytest.fixture
def run_mocks():
    names = ['Infojobs', 'Linkedin', 'Glassdoor', 'Tecnoempleo', 'Indeed']
    # Patch the actual executor modules, not inside BaseExecutor
    patchers = {name: patch(f'scrapper.executor.{name}Executor.{name}Executor') for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

class MockBaseExecutor(BaseExecutor):
    def _create_service(self, mysql):
        return MagicMock()
    def _process_keyword(self, keyword, start_page):
        pass

class TestExecutor:
    @pytest.mark.parametrize("name", ['Infojobs'])
    def test_create_executor(self, mocks, run_mocks, name):
        mock_executor_cls = run_mocks[name]
        # Patch get_debug to return True
        with patch('scrapper.executor.BaseExecutor.get_debug', return_value=True):
            executor = BaseExecutor.create(name.lower(), mocks['sel'], mocks['pm'])
            mock_executor_cls.assert_called_with(mocks['sel'], mocks['pm'], True)

    def test_execute_preload(self, mocks):
        # Use concrete class for testing base methods
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "TestSite"
        props = {}
        
        with patch.object(executor, 'run') as mock_run:
            executor.execute_preload(props)
            mock_run.assert_called_with(preload_page=True)
            assert props['preloaded'] is True

    def test_execute(self, mocks):
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "TestSite"
        props = {}
        
        with patch.object(executor, 'run') as mock_run:
            executor.execute(props)
            mock_run.assert_called_with(preload_page=False)
            mocks['pm'].update_last_execution.assert_called()

    def test_execute_exception(self, mocks):
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "TestSite"
        props = {}
        
        # Simulate exception in run
        with patch.object(executor, 'run', side_effect=Exception("Scrapper failed")):
            executor.execute(props)
        
        # Verify set_error is called
        mocks['pm'].set_error.assert_called_with(executor.site_name_key, "Scrapper failed")
        # Verify last_execution updated to None
        mocks['pm'].update_last_execution.assert_called_with(executor.site_name_key, None)

    def test_preload_failure_sets_error_in_persistence(self, mocks):
        # Setup - patch the executor to test execute_preload directly
        name = "infojobs"
        properties = {"preloaded": False}
        
        # We need to simulate the class/instance structure expected by execute_preload
        # BaseExecutor.execute_preload calls self.run(preload_page=True)
        # We can reuse MockBaseExecutor
        
        executor = MockBaseExecutor(mocks['sel'], mocks['pm'], False)
        executor.site_name = "INFOJOBS"

        
        with patch.object(executor, 'run', side_effect=Exception("Preload Error")):
            # Call bound method
            result = executor.execute_preload(properties)
            
            # Verify
            assert result is True
            assert properties["preloaded"] is False
            mocks['pm'].set_error.assert_called_once()
            args = mocks['pm'].set_error.call_args[0]
            assert args[0] == "Infojobs"
            assert "Preload Error" in args[1]


class TestProcessPageUrl:
    def test_linkedin_url(self, mocks):
        url = "https://www.linkedin.com/jobs/view/123"
        with patch('scrapper.executor.LinkedinExecutor.LinkedinExecutor.process_specific_url') as mock_process:
            BaseExecutor.process_page_url(url)
            mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            BaseExecutor.process_page_url(url)
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    def test_unknown_url(self):
        url = "https://www.google.com"
        with patch('scrapper.executor.LinkedinExecutor.LinkedinExecutor.process_specific_url') as mock_process:
            BaseExecutor.process_page_url(url)
            mock_process.assert_not_called()
