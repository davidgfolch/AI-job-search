import pytest
from unittest.mock import patch, MagicMock
from scrapper.scrapper_config import (
    CLOSE_TAB, NEW_ARCH, SCRAPPERS, TIMER
)
from scrapper.scrapper_execution import (
    executeScrapperPreload, executeScrapper,
    runScrapper, runScrapperPageUrl, hasNewArchitecture
)

@pytest.fixture
def mocks():
    sel = MagicMock()
    pm = MagicMock()
    cont = MagicMock()
    return {'sel': sel, 'pm': pm, 'cont': cont}

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
    def test_preload(self, mocks, run_mocks, in_tabs, preload, close_tab, error):
        with patch('scrapper.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close_tab} if close_tab else {}
            if error: run_mocks['infojobs'].side_effect = error
            executeScrapperPreload('infojobs', props, mocks['sel'], mocks['cont'], mocks['pm'])
            assert props.get('preloaded') is (False if error else preload)
            run_mocks['infojobs'].assert_called_with(mocks['sel'], True, mocks['pm'])

    @pytest.mark.parametrize("in_tabs, close, error", [
        (False, False, None), (True, False, None), (True, True, None), (False, False, Exception)
    ])
    def test_execute(self, mocks, run_mocks, in_tabs, close, error):
        with patch('scrapper.scrapper_execution.RUN_IN_TABS', in_tabs):
            props = {CLOSE_TAB: close} if close else {}
            if error: run_mocks['infojobs'].side_effect = error
            executeScrapper('infojobs', props, mocks['pm'], mocks['sel'], mocks['cont'])
            if in_tabs: mocks['sel'].tab.assert_called()
            if close: mocks['sel'].tabClose.assert_called()
            run_mocks['infojobs'].assert_called_with(mocks['sel'], False, mocks['pm'])

class TestNewArchitecture:
    def test_preload(self, mocks):
        srv = MagicMock()
        srv.executeScrapping.return_value = {'login_success': True}
        mocks['cont'].get_scrapping_service.return_value = srv
        props = {NEW_ARCH: True}
        executeScrapperPreload('Linkedin', props, mocks['sel'], mocks['cont'], mocks['pm'])
        srv.executeScrapping.assert_called_with(mocks['sel'], [], preloadOnly=True)
        assert props['preloaded'] is True

    def test_execution(self, mocks):
        srv = MagicMock()
        mocks['cont'].get_scrapping_service.return_value = srv
        props = {NEW_ARCH: True}
        with patch('scrapper.scrapper_execution.getEnv', return_value='kw'):
            executeScrapper('Linkedin', props, mocks['pm'], mocks['sel'], mocks['cont'])
        srv.executeScrapping.assert_called_with(mocks['sel'], ['kw'], preloadOnly=False, persistenceManager=mocks['pm'])

class TestExecutionHelpers:
    @pytest.mark.parametrize("name", ['linkedin', 'infojobs', 'tecnoempleo', 'glassdoor', 'indeed'])
    def test_run_scrapper(self, name, run_mocks, mocks):
        runScrapper(name, False, mocks['pm'], mocks['sel'])
        run_mocks[name].assert_called_once_with(mocks['sel'], False, mocks['pm'])

    def test_has_new_architecture(self, mocks):
        mocks['cont'].get_scrapping_service.return_value = MagicMock()
        assert hasNewArchitecture('L', {NEW_ARCH: True}, mocks['cont']) is True
        mocks['cont'].get_scrapping_service.side_effect = Exception
        assert hasNewArchitecture('L', {NEW_ARCH: True}, mocks['cont']) is False

class TestRunScrapperPageUrl:
    def test_linkedin_url(self, mocks):
        url = "https://www.linkedin.com/jobs/view/123"
        with patch('scrapper.scrapper_execution.linkedin.processUrl') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_called_once_with(url)

    def test_unimplemented_scrapper(self):
        url = "https://www.infojobs.net/job/123"
        with pytest.raises(Exception) as excinfo:
            runScrapperPageUrl(url)
        assert "Invalid scrapper web page name Infojobs, only linkedin is implemented" in str(excinfo.value)

    def test_unknown_url(self):
        url = "https://www.google.com"
        with patch('scrapper.scrapper_execution.linkedin.processUrl') as mock_process:
            runScrapperPageUrl(url)
            mock_process.assert_not_called()
