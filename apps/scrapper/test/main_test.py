import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from scrapper.main import CLOSE_TAB, NEW_ARCH, FUNCTION, IGNORE_AUTORUN, SCRAPPERS, TIMER, runAllScrappers, runSpecifiedScrappers, timeExpired, validScrapperName, executeScrapperPreload, executeScrapper, runPreload


@pytest.fixture
def mock_scrappers():
    with patch.dict(SCRAPPERS, {
        'Infojobs': {FUNCTION: MagicMock(), TIMER: 7200},
        'Linkedin': {FUNCTION: MagicMock(), TIMER: 3600, CLOSE_TAB: True},
        'Glassdoor': {FUNCTION: MagicMock(), TIMER: 10800},
        'Tecnoempleo': {FUNCTION: MagicMock(), TIMER: 7200},
        'Indeed': {FUNCTION: MagicMock(), TIMER: 10800, IGNORE_AUTORUN: True},
    }):
        yield


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


def mockPropertiesFunction(sideEffect=None):
    mockFnc = MagicMock(side_effect=sideEffect)
    return {FUNCTION: mockFnc, 'preloaded': None}


@pytest.mark.parametrize("runInTabs, exception, preloaded", [
    (False, False, True),
    (True, False, True),
    (False, True, False),
])
def testExecuteScrapperPreload(mock_selenium, runInTabs, exception, preloaded):
    properties = mockPropertiesFunction(Exception("Test error") if exception else None)
    with patch('scrapper.main.RUN_IN_TABS', runInTabs):
        executeScrapperPreload('', properties)
    if not exception:
        properties[FUNCTION].assert_called_once_with(mock_selenium, True)
    if runInTabs:
        mock_selenium.tab.assert_called_once_with('')
    assert properties['preloaded'] is preloaded


class TestExecuteScrapper:
    def test_success(self, mock_selenium):
        properties = mockPropertiesFunction()
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        properties[FUNCTION].assert_called_once_with(mock_selenium, False)

    def test_with_tabs(self, mock_selenium):
        properties = mockPropertiesFunction()
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('', properties)
        assert mock_selenium.tab.call_count == 1
        properties[FUNCTION].assert_called_once_with(mock_selenium, False)

    def test_with_close_tab(self, mock_selenium):
        properties = mockPropertiesFunction()
        properties[CLOSE_TAB] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('', properties)
        mock_selenium.tabClose.assert_called_once_with('')
        mock_selenium.tab.assert_called()

    def test_exception(self, mock_selenium):
        properties = mockPropertiesFunction(Exception("Test error"))
        properties['lastExecution'] = datetime(2025, 1, 1)
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        assert properties['lastExecution'] is None
        properties[FUNCTION].assert_called_once_with(mock_selenium, False)

    def test_keyboard_interrupt(self, mock_selenium):
        properties = mockPropertiesFunction(KeyboardInterrupt())
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        properties[FUNCTION].assert_called_once_with(mock_selenium, False)


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
    def test_basic(self, mock_scrappers, mock_selenium, reset_scrappers):
        """Test basic execution of all scrappers"""
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', False), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        SCRAPPERS['Infojobs'][FUNCTION].assert_called()
        SCRAPPERS['Linkedin'][FUNCTION].assert_called()
        SCRAPPERS['Glassdoor'][FUNCTION].assert_called()
        SCRAPPERS['Tecnoempleo'][FUNCTION].assert_called()
        assert SCRAPPERS['Indeed'][FUNCTION].call_count == 0

    def test_with_starting(self, mock_scrappers, mock_selenium, reset_scrappers):
        """Test starting at specific scrapper"""
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', False), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=True, startingAt='Linkedin', loops=1)
        assert SCRAPPERS['Infojobs'][FUNCTION].call_count == 0
        assert SCRAPPERS['Tecnoempleo'][FUNCTION].call_count == 0
        SCRAPPERS['Linkedin'][FUNCTION].assert_called()
        SCRAPPERS['Glassdoor'][FUNCTION].assert_called()

    def test_with_tabs(self, mock_scrappers, mock_selenium, reset_scrappers):
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', True), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        assert mock_selenium.tab.call_count >= 4


class TestRunSpecifiedScrappers:
    def test_single(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs'])
        assert SCRAPPERS['Infojobs'][FUNCTION].call_count == 2
        assert SCRAPPERS['Linkedin'][FUNCTION].call_count == 0

    def test_multiple(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'Linkedin', 'Glassdoor'])
        assert SCRAPPERS['Infojobs'][FUNCTION].call_count == 2
        assert SCRAPPERS['Linkedin'][FUNCTION].call_count == 2
        assert SCRAPPERS['Glassdoor'][FUNCTION].call_count == 2
        assert SCRAPPERS['Indeed'][FUNCTION].call_count == 0

    def test_mixed_valid_invalid(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'InvalidScrapper', 'Linkedin'])
        assert SCRAPPERS['Infojobs'][FUNCTION].call_count == 2
        assert SCRAPPERS['Linkedin'][FUNCTION].call_count == 2

    def test_case_insensitive(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['infojobs', 'LINKEDIN'])
        assert SCRAPPERS['Infojobs'][FUNCTION].call_count == 2
        assert SCRAPPERS['Linkedin'][FUNCTION].call_count == 2

    def test_with_preloaded(self, mock_scrappers, mock_selenium):
        SCRAPPERS['Infojobs']['preloaded'] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            runSpecifiedScrappers(['Infojobs'])
        SCRAPPERS['Infojobs'][FUNCTION].assert_called()


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
        properties = {FUNCTION: MagicMock(), NEW_ARCH: True}
        with patch('scrapper.main.SCRAPPERS', {'Linkedin': {FUNCTION: MagicMock(), NEW_ARCH: True}}):
            executeScrapperPreload('Linkedin', properties)
        mock_scrapperService.executeScrapping.assert_called_once_with(mock_selenium, [], preloadOnly=True)
        assert properties['preloaded'] is True

    def test_new_architecture_preload_failure_fallback(self, mock_selenium, mock_container, mock_scrapperService):
        """Test new architecture preload failure falls back to old method"""
        mock_container.get_scrapping_service.return_value = mock_scrapperService
        mock_scrapperService.executeScrapping.return_value = {'login_success': False}
        properties = {FUNCTION: MagicMock()}
        executeScrapperPreload('Linkedin', properties)
        properties[FUNCTION].assert_called_once_with(mock_selenium, True)
        assert properties['preloaded'] is True

    def test_new_architecture_scrapping_success(self, mock_selenium, mock_container, mock_scrapperService):
        """Test new architecture scrapping execution"""
        mock_container.get_scrapping_service.return_value = mock_scrapperService
        properties = {FUNCTION: MagicMock(), NEW_ARCH: True}
        with patch.dict('scrapper.main.SCRAPPERS', {'Linkedin': {FUNCTION: MagicMock(), NEW_ARCH: True}}), \
                patch('scrapper.main.getEnv', return_value='java,python'):
            executeScrapper('Linkedin', properties)
        mock_scrapperService.executeScrapping.assert_called_once_with(
            mock_selenium, ['java', 'python'], preloadOnly=False
        )

    def test_new_architecture_scrapping_exception_fallback(self, mock_selenium, mock_container):
        """Test new architecture exception falls back to old method"""
        mock_container.get_scrapping_service.side_effect = Exception("Container error")
        properties = {FUNCTION: MagicMock()}
        executeScrapper('Linkedin', properties)
        properties[FUNCTION].assert_called_once_with(mock_selenium, False)

    def test_non_linkedin_scrapper_uses_old_architecture(self, mock_selenium):
        """Test non-LinkedIn scrappers still use old architecture"""
        properties = {FUNCTION: MagicMock()}
        executeScrapperPreload('Infojobs', properties)
        executeScrapper('Infojobs', properties)
        assert properties[FUNCTION].call_count == 2
        properties[FUNCTION].assert_any_call(mock_selenium, True)
        properties[FUNCTION].assert_any_call(mock_selenium, False)
