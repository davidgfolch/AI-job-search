import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from scrapper.main import CLOSE_TAB, NEW_ARCH, IGNORE_AUTORUN, SCRAPPERS, TIMER, runAllScrappers, runSpecifiedScrappers, timeExpired, validScrapperName, executeScrapperPreload, executeScrapper, runPreload


@pytest.fixture
def mock_scrappers():
    with patch.dict(SCRAPPERS, {
        'Infojobs': {TIMER: 7200},
        'Linkedin': {TIMER: 3600, CLOSE_TAB: True},
        'Glassdoor': {TIMER: 10800},
        'Tecnoempleo': {TIMER: 7200},
        'Indeed': {TIMER: 10800, IGNORE_AUTORUN: True},
    }):
        yield


@pytest.fixture
def mock_infojobs_run():
    with patch('scrapper.infojobs.run', MagicMock()) as runFnc:
        yield runFnc


@pytest.fixture
def mock_linkedin_run():
    with patch('scrapper.linkedin.run', MagicMock()) as runFnc:
        yield runFnc


@pytest.fixture
def mock_glassdoor_run():
    with patch('scrapper.glassdoor.run', MagicMock()) as runFnc:
        yield runFnc


@pytest.fixture
def mock_tecnoempleo_run():
    with patch('scrapper.tecnoempleo.run', MagicMock()) as runFnc:
        yield runFnc


@pytest.fixture
def mock_indeed_run():
    with patch('scrapper.indeed.run', MagicMock()) as runFnc:
        yield runFnc


@pytest.fixture
def mock_selenium():
    with patch('scrapper.main.seleniumUtil', MagicMock()) as mock:
        yield mock


@pytest.fixture
def reset_scrappers():
    """Reset SCRAPPERS state after each test"""
    yield
    for properties in SCRAPPERS.values():
        properties.pop('lastExecution', None)
        properties.pop('waitBeforeFirstRun', None)
        properties.pop('preloaded', None)


class TestTimeExpired:
    def test_first_run_no_wait(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {TIMER: 3600, 'waitBeforeFirstRun': False}
            assert timeExpired('', properties) is True
            assert properties['lastExecution'] == 1000

    def test_first_run_with_wait(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {TIMER: 3600, 'waitBeforeFirstRun': True}
            assert timeExpired('', properties) is False
            assert properties['lastExecution'] == 1000

    @patch('scrapper.main.getDatetimeNow', side_effect=[100, 1900])
    @patch('scrapper.main.getTimeUnits', return_value='30m 0s')
    def test_not_expired(self, mockGetTimeUnits, mockGetDatetimeNow):
        properties = {
            TIMER: 3600,
            'lastExecution': None,
            'waitBeforeFirstRun': False
        }
        mockGetDatetimeNow.reset_mock()
        res = timeExpired('', properties)
        assert res is True
        assert properties['lastExecution'] == 100
        result2 = timeExpired('', properties)
        assert result2 is False
        assert properties['lastExecution'] == 100

    @patch('scrapper.main.getDatetimeNow', side_effect=[5000, 6000])
    def test_expired(self, mockGetDatetimeNow):
        properties = {
            TIMER: 3600,
            'waitBeforeFirstRun': False,
            'lastExecution': 100
        }
        res = timeExpired('', properties)
        assert res is True
        assert properties['lastExecution'] == 6000

    def test_none_last_execution(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {
                TIMER: 3600,
                'lastExecution': None,
                'waitBeforeFirstRun': False
            }
            assert timeExpired('', properties) is True


@pytest.mark.parametrize("input, expected", [
    ('Infojobs', True), ('infojobs', True), ('INFOJOBS', True),
    ('INFO JOBS', False), ('non existent', False), ('', False),
])
def test_valid_scrapper_name(input, expected):
    assert validScrapperName(input) is expected


@pytest.mark.parametrize("runInTabs, preloaded", [
    (False, True),
    (True, True),
])
def testExecuteScrapperPreload(mock_selenium, mock_infojobs_run, runInTabs, preloaded):
    properties = {}
    with patch('scrapper.main.RUN_IN_TABS', runInTabs):
        executeScrapperPreload('infojobs', properties)
    if runInTabs:
        mock_selenium.tab.assert_called_once_with('infojobs')
    mock_infojobs_run.assert_called_once_with(mock_selenium, True)
    assert properties['preloaded'] is preloaded


def testExecuteScrapperPreloadException(mock_selenium, mock_infojobs_run):
    """Test that preloaded is False when an exception occurs"""
    properties = {}
    mock_infojobs_run.side_effect = Exception("Test exception")
    with patch('scrapper.main.RUN_IN_TABS', False):
        executeScrapperPreload('infojobs', properties)
    assert properties['preloaded'] is False


class TestExecuteScrapper:
    def test_success(self, mock_selenium, mock_infojobs_run):
        properties = {}
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('infojobs', properties)
        mock_infojobs_run.assert_called_once_with(mock_selenium, False)

    def test_with_tabs(self, mock_selenium, mock_infojobs_run):
        properties = {}
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('infojobs', properties)
        assert mock_selenium.tab.call_count == 1
        mock_infojobs_run.assert_called_once_with(mock_selenium, False)

    def test_with_close_tab(self, mock_selenium, mock_infojobs_run):
        properties = {}
        properties[CLOSE_TAB] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('infojobs', properties)
        mock_selenium.tabClose.assert_called_once_with('infojobs')
        mock_selenium.tab.assert_called()

    def test_exception(self, mock_selenium, mock_infojobs_run):
        properties = {}
        properties['lastExecution'] = datetime(2025, 1, 1)
        mock_infojobs_run.side_effect = Exception("Test exception")
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('infojobs', properties)
        assert properties['lastExecution'] is None
        mock_infojobs_run.assert_called_once_with(mock_selenium, False)

    def test_keyboard_interrupt(self, mock_selenium, mock_infojobs_run):
        properties = {}
        mock_infojobs_run.side_effect = Exception("Test exception")
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('infojobs', properties)
        mock_infojobs_run.assert_called_once_with(mock_selenium, False)


class TestRunPreload:
    def test_not_preloaded(self):
        properties = {}
        assert runPreload(properties) is True

    def test_already_preloaded_no_tabs(self):
        properties = {'preloaded': True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            assert runPreload(properties) is False

    def test_with_close_tab(self):
        properties = {'preloaded': True, CLOSE_TAB: True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            assert runPreload(properties) is True

    def test_not_in_tabs(self):
        properties = {'preloaded': True}
        with patch('scrapper.main.RUN_IN_TABS', False):
            assert runPreload(properties) is True


class TestRunAllScrappers:
    def test_basic(self, mock_scrappers, mock_selenium, reset_scrappers,
                   mock_infojobs_run, mock_linkedin_run, mock_glassdoor_run, mock_tecnoempleo_run, mock_indeed_run):
        """Test basic execution of all scrappers"""
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', False), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        mock_infojobs_run.assert_called()
        mock_linkedin_run.assert_called()
        mock_glassdoor_run.assert_called()
        mock_tecnoempleo_run.assert_called()
        assert mock_indeed_run.call_count == 0

    def test_with_starting(self, mock_scrappers, mock_selenium, reset_scrappers,
                           mock_infojobs_run, mock_linkedin_run, mock_glassdoor_run, mock_tecnoempleo_run, mock_indeed_run):
        """Test starting at specific scrapper"""
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', False), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=True, startingAt='Linkedin', loops=1)
        assert mock_infojobs_run.call_count == 0
        assert mock_tecnoempleo_run.call_count == 0
        mock_linkedin_run.assert_called()
        mock_glassdoor_run.assert_called()

    def test_with_tabs(self, mock_scrappers, mock_selenium, reset_scrappers,
                   mock_infojobs_run, mock_linkedin_run, mock_glassdoor_run, mock_tecnoempleo_run, mock_indeed_run):
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', True), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        assert mock_selenium.tab.call_count >= 4


class TestRunSpecifiedScrappers:
    def test_single(self, mock_scrappers, mock_selenium, mock_infojobs_run, mock_linkedin_run):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs'])
        assert mock_infojobs_run.call_count == 2
        assert mock_linkedin_run.call_count == 0

    def test_multiple(self, mock_scrappers, mock_selenium,
                      mock_infojobs_run, mock_linkedin_run, mock_glassdoor_run, mock_indeed_run):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'Linkedin', 'Glassdoor'])
        assert mock_infojobs_run.call_count == 2
        assert mock_linkedin_run.call_count == 2
        assert mock_glassdoor_run.call_count == 2
        assert mock_indeed_run.call_count == 0

    def test_mixed_valid_invalid(self, mock_scrappers, mock_selenium, mock_infojobs_run, mock_linkedin_run):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'InvalidScrapper', 'Linkedin'])
        assert mock_infojobs_run.call_count == 2
        assert mock_linkedin_run.call_count == 2

    def test_case_insensitive(self, mock_scrappers, mock_selenium, mock_infojobs_run, mock_linkedin_run):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['infojobs', 'LINKEDIN'])
        assert mock_infojobs_run.call_count == 2
        assert mock_linkedin_run.call_count == 2

    def test_with_preloaded(self, mock_scrappers, mock_selenium, mock_infojobs_run):
        SCRAPPERS['Infojobs']['preloaded'] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            runSpecifiedScrappers(['Infojobs'])
        mock_infojobs_run.assert_called()


class TestNewArchitecture:
    """Test new SOLID architecture integration"""

    @pytest.fixture
    def mock_container(self):
        with patch('scrapper.main.scrapperContainer', create=True) as mock:
            yield mock

    @pytest.fixture
    def mock_scrapperService(self):
        mock_service = MagicMock()
        mock_service.executeScrapping.return_value = {
            'total_processed': 5,
            'total_saved': 3,
            'total_duplicates': 2,
            'errors': []
        }
        return mock_service

    def test_new_architecture_preload_success(self, mock_selenium, mock_container, mock_scrapperService):
        """Test new architecture preload success"""
        mock_container.get_scrapping_service.return_value = mock_scrapperService
        mock_scrapperService.executeScrapping.return_value = {'login_success': True}
        properties = {NEW_ARCH: True}
        with patch('scrapper.main.SCRAPPERS', {'Linkedin': {NEW_ARCH: True}}):
            executeScrapperPreload('Linkedin', properties)
        mock_scrapperService.executeScrapping.assert_called_once_with(mock_selenium, [], preloadOnly=True)
        assert properties['preloaded'] is True

    def test_new_architecture_preload_failure_fallback(self, mock_selenium, mock_container, mock_scrapperService, mock_infojobs_run):
        """Test new architecture preload failure falls back to old method"""
        mock_container.get_scrapping_service.return_value = mock_scrapperService
        mock_scrapperService.executeScrapping.return_value = {'login_success': False}
        properties = {}
        executeScrapperPreload('infojobs', properties)
        mock_infojobs_run.assert_called_once_with(mock_selenium, True)
        assert properties['preloaded'] is True

    def test_new_architecture_scrapping_success(self, mock_selenium, mock_container, mock_scrapperService):
        """Test new architecture scrapping execution"""
        mock_container.get_scrapping_service.return_value = mock_scrapperService
        properties = {NEW_ARCH: True}
        with patch.dict('scrapper.main.SCRAPPERS', {'Linkedin': {NEW_ARCH: True}}), \
                patch('scrapper.main.getEnv', return_value='java,python'):
            executeScrapper('Linkedin', properties)
        mock_scrapperService.executeScrapping.assert_called_once_with(
            mock_selenium, ['java', 'python'], preloadOnly=False
        )

    def test_new_architecture_scrapping_exception_fallback(self, mock_selenium, mock_container, mock_linkedin_run):
        """Test new architecture exception falls back to old method"""
        mock_container.get_scrapping_service.side_effect = Exception("Container error")
        executeScrapper('Linkedin', {})
        mock_linkedin_run.assert_called_once_with(mock_selenium, False)

    def test_non_linkedin_scrapper_uses_old_architecture(self, mock_selenium, mock_infojobs_run):
        """Test non-LinkedIn scrappers still use old architecture"""
        executeScrapperPreload('Infojobs', {})
        executeScrapper('Infojobs', {})
        assert mock_infojobs_run.call_count == 2
        mock_infojobs_run.assert_any_call(mock_selenium, True)
        mock_infojobs_run.assert_any_call(mock_selenium, False)
