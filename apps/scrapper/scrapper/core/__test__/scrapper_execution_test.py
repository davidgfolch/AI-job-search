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
    names = ['infojobs', 'linkedin', 'glassdoor', 'tecnoempleo', 'indeed']
    patchers = {name: patch(f'scrapper.{name}.run', MagicMock()) for name in names}
    yield {name: p.start() for name, p in patchers.items()}
    for p in patchers.values(): p.stop()

class TestExecuteScrapper:
    @pytest.mark.parametrize("in_tabs, preload, close_tab, error", [
        (False, True, False, None), (True, True, False, None), (False, False, False, Exception)
    ])
    def test_preload(self, execution, mocks, run_mocks, in_tabs, preload, close_tab, error):
        with patch('scrapper.core.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close_tab} if close_tab else {}
            if error: run_mocks['infojobs'].side_effect = error
            execution.executeScrapperPreload('infojobs', props)
            assert props.get('preloaded') is (False if error else preload)
            run_mocks['infojobs'].assert_called_with(mocks['sel'], True, mocks['pm'])

    @pytest.mark.parametrize("in_tabs, close, error", [
        (False, False, None), (True, False, None), (True, True, None), (False, False, Exception)
    ])
    def test_execute(self, execution, mocks, run_mocks, in_tabs, close, error):
        with patch('scrapper.core.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close} if close else {}
            if error: run_mocks['infojobs'].side_effect = error
            execution.executeScrapper('infojobs', props)
            if in_tabs: mocks['sel'].tab.assert_called()
            if close: mocks['sel'].tabClose.assert_called()
            run_mocks['infojobs'].assert_called_with(mocks['sel'], False, mocks['pm'])

class TestExecutionHelpers:
    @pytest.mark.parametrize("name", ['linkedin', 'infojobs', 'tecnoempleo', 'glassdoor', 'indeed'])
    def test_run_scrapper(self, name, execution, run_mocks, mocks):
        execution.runScrapper(name, False)
        run_mocks[name].assert_called_once_with(mocks['sel'], False, mocks['pm'])

class TestRunScrapperPageUrl:
    def test_linkedin_url(self, mocks):
        url = "https://www.linkedin.com/jobs/view/123"
        with patch('scrapper.core.scrapper_execution.linkedin.processUrl') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            runScrapperPageUrl(url)
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    def test_unknown_url(self):
        url = "https://www.google.com"
        with patch('scrapper.core.scrapper_execution.linkedin.processUrl') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_not_called()
