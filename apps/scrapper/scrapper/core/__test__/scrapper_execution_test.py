import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_config import (
    CLOSE_TAB, SCRAPPERS, TIMER
)
from scrapper.core.scrapper_execution import (
    ScrapperExecution, runScrapperPageUrl
)

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    return {'sel': sel, 'pm': pm}

@pytest.fixture
def execution(mocks):
    return ScrapperExecution(mocks['pm'], mocks['sel'])

@pytest.fixture
def run_mocks():
    names = ['Infojobs', 'Linkedin', 'Glassdoor', 'Tecnoempleo', 'Indeed']
    patchers = {name: patch(f'scrapper.core.scrapper_execution.{name}Executor') for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

class TestExecuteScrapper:
    @pytest.mark.parametrize("in_tabs, preload, close_tab, error", [
        (False, True, False, None), (True, True, False, None), (False, False, False, Exception)
    ])
    def test_preload(self, execution, mocks, run_mocks, in_tabs, preload, close_tab, error):
        with patch('scrapper.core.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close_tab} if close_tab else {}
            mock_executor_cls = run_mocks['Infojobs']
            mock_instance = mock_executor_cls.return_value
            
            if error: 
                mock_instance.run.side_effect = error
            
            execution.executeScrapperPreload('infojobs', props)
            
            assert props.get('preloaded') is (False if error else preload)
            mock_executor_cls.assert_called_with(mocks['sel'], mocks['pm'])
            mock_instance.run.assert_called_with(True)

    @pytest.mark.parametrize("in_tabs, close, error", [
        (False, False, None), (True, False, None), (True, True, None), (False, False, Exception)
    ])
    def test_execute(self, execution, mocks, run_mocks, in_tabs, close, error):
        with patch('scrapper.core.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close} if close else {}
            mock_executor_cls = run_mocks['Infojobs']
            mock_instance = mock_executor_cls.return_value
            
            if error: 
                mock_instance.run.side_effect = error
            
            execution.executeScrapper('infojobs', props)
            
            if in_tabs: mocks['sel'].tab.assert_called()
            if close: mocks['sel'].tabClose.assert_called()
            
            mock_executor_cls.assert_called_with(mocks['sel'], mocks['pm'])
            mock_instance.run.assert_called_with(False)

class TestExecutionHelpers:
    @pytest.mark.parametrize("name", ['Linkedin', 'Infojobs', 'Tecnoempleo', 'Glassdoor', 'Indeed'])
    def test_run_scrapper(self, name, execution, run_mocks, mocks):
        execution.runScrapper(name.lower(), False)
        
        mock_executor_cls = run_mocks[name]
        mock_instance = mock_executor_cls.return_value
        
        mock_executor_cls.assert_called_once_with(mocks['sel'], mocks['pm'])
        mock_instance.run.assert_called_once_with(False)

class TestRunScrapperPageUrl:
    def test_linkedin_url(self, mocks):
        url = "https://www.linkedin.com/jobs/view/123"
        with patch('scrapper.core.scrapper_execution.LinkedinExecutor.process_specific_url') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            runScrapperPageUrl(url)
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    def test_unknown_url(self):
        url = "https://www.google.com"
        with patch('scrapper.core.scrapper_execution.LinkedinExecutor.process_specific_url') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_not_called()
