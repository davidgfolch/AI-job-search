import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call

from scrapper.main import (
    SCRAPPERS,
    runAllScrappers,
    runSpecifiedScrappers,
    timeExpired,
    validScrapperName,
    executeScrapperPreload,
    executeScrapper,
    runPreload
)


@pytest.fixture
def mock_scrappers():
    with patch.dict(SCRAPPERS, {
        'Infojobs': {'function': MagicMock(), 'timer': 7200},
        'Linkedin': {'function': MagicMock(), 'timer': 3600, 'closeTab': True},
        'Glassdoor': {'function': MagicMock(), 'timer': 10800},
        'Tecnoempleo': {'function': MagicMock(), 'timer': 7200},
        'Indeed': {'function': MagicMock(), 'timer': 10800, 'ignoreAutoRun': True},
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


# Tests for timeExpired function
class TestTimeExpired:
    def first_run_no_wait(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {'timer': 3600, 'waitBeforeFirstRun': False}
            assert timeExpired('', properties) is True
            assert properties['lastExecution'] == 2000

    def first_run_with_wait(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {'timer': 3600, 'waitBeforeFirstRun': True}
            assert timeExpired('', properties) is False
            assert properties['lastExecution'] == 1000

    @patch('scrapper.main.getDatetimeNow', side_effect=[100, 1900])
    @patch('scrapper.main.getTimeUnits', return_value='30m 0s')
    def not_expired(self, mockGetTimeUnits, mockGetDatetimeNow):
        properties = {
            'timer': 3600,  # 1 hour in seconds
            'lastExecution': None,
            'waitBeforeFirstRun': False
        }
        mockGetDatetimeNow.reset_mock()
        res = timeExpired('', properties)
        assert res is True  # First run always returns True
        assert properties['lastExecution'] == 100
        result2 = timeExpired('', properties)
        assert result2 is False
        assert properties['lastExecution'] == 100  # Should not update

    @patch('scrapper.main.getDatetimeNow', side_effect=[5000, 6000])
    def expired(self, mockGetDatetimeNow):
        properties = {
            'timer': 3600,  # 1 hour in seconds
            'waitBeforeFirstRun': False,
            'lastExecution': 100  # Set initial lastExecution
        }
        res = timeExpired('', properties)
        assert res is True
        assert properties['lastExecution'] == 6000  # Should update to new time

    def none_last_execution(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {
                'timer': 3600,
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


class TestExecuteScrapperPreload:
    def success(self, mock_selenium):
        mock_function = MagicMock()
        properties = {'function': mock_function}
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapperPreload('', properties)
        mock_function.assert_called_once_with(mock_selenium, True)
        assert properties['preloaded'] is True

    def with_tabs(self, mock_selenium):
        mock_function = MagicMock()
        properties = {'function': mock_function}
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapperPreload('', properties)
        mock_selenium.tab.assert_called_once_with('')
        mock_function.assert_called_once_with(mock_selenium, True)
        assert properties['preloaded'] is True

    def exception(self, mock_selenium):
        mock_function = MagicMock(side_effect=Exception("Test error"))
        properties = {'function': mock_function}
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapperPreload('', properties)
        assert properties['preloaded'] is False


class TestExecuteScrapper:
    def test_executeScrapper_success(self, mock_selenium):
        mock_function = MagicMock()
        properties = {'function': mock_function}
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        mock_function.assert_called_once_with(mock_selenium, False)

    def test_executeScrapper_with_tabs(self, mock_selenium):
        mock_function = MagicMock()
        properties = {'function': mock_function}
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('', properties)
        assert mock_selenium.tab.call_count == 1  # Only the finally block call
        mock_function.assert_called_once_with(mock_selenium, False)

    def test_executeScrapper_with_close_tab(self, mock_selenium):
        mock_function = MagicMock()
        properties = {'function': mock_function, 'closeTab': True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('', properties)
        mock_selenium.tabClose.assert_called_once_with('')

    def test_executeScrapper_exception(self, mock_selenium):
        mock_function = MagicMock(side_effect=Exception("Test error"))
        properties = {'function': mock_function, 'lastExecution': datetime(2025, 1, 1)}
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        assert properties['lastExecution'] is None

    def test_executeScrapper_keyboard_interrupt(self, mock_selenium):
        mock_function = MagicMock(side_effect=KeyboardInterrupt())
        properties = {'function': mock_function}
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        mock_function.assert_called_once()


class TestRunPreload:
    def test_runPreload_not_preloaded(self):
        properties = {}
        assert runPreload(properties) is True

    def test_runPreload_already_preloaded_no_tabs(self):
        properties = {'preloaded': True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            assert runPreload(properties) is False

    def test_runPreload_with_close_tab(self):
        properties = {'preloaded': True, 'closeTab': True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            assert runPreload(properties) is True

    def test_runPreload_not_in_tabs(self):
        properties = {'preloaded': True}
        with patch('scrapper.main.RUN_IN_TABS', False):
            assert runPreload(properties) is True


class TestRunAllScrappers:
    def test_runAllScrappers_basic(self, mock_scrappers, mock_selenium, reset_scrappers):
        """Test basic execution of all scrappers"""
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', False), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        SCRAPPERS['Infojobs']['function'].assert_called()
        SCRAPPERS['Linkedin']['function'].assert_called()
        SCRAPPERS['Glassdoor']['function'].assert_called()
        SCRAPPERS['Tecnoempleo']['function'].assert_called()
        assert SCRAPPERS['Indeed']['function'].call_count == 0

    def test_runAllScrappers_with_starting(self, mock_scrappers, mock_selenium, reset_scrappers):
        """Test starting at specific scrapper"""
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', False), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=True, startingAt='Linkedin', loops=1)
        assert SCRAPPERS['Infojobs']['function'].call_count == 0
        assert SCRAPPERS['Tecnoempleo']['function'].call_count == 0
        SCRAPPERS['Linkedin']['function'].assert_called()
        SCRAPPERS['Glassdoor']['function'].assert_called()

    def test_runAllScrappers_with_tabs(self, mock_scrappers, mock_selenium, reset_scrappers):
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', True), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        assert mock_selenium.tab.call_count >= 4


class TestRunSpecifiedScrappers:
    def test_runSpecifiedScrappers_single(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 2
        assert SCRAPPERS['Linkedin']['function'].call_count == 0

    def test_runSpecifiedScrappers_multiple(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'Linkedin', 'Glassdoor'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 2
        assert SCRAPPERS['Linkedin']['function'].call_count == 2
        assert SCRAPPERS['Glassdoor']['function'].call_count == 2
        assert SCRAPPERS['Indeed']['function'].call_count == 0

    def test_runSpecifiedScrappers_mixed_valid_invalid(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'InvalidScrapper', 'Linkedin'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 2
        assert SCRAPPERS['Linkedin']['function'].call_count == 2

    def test_runSpecifiedScrappers_case_insensitive(self, mock_scrappers, mock_selenium):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['infojobs', 'LINKEDIN'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 2
        assert SCRAPPERS['Linkedin']['function'].call_count == 2

    def test_runSpecifiedScrappers_with_preloaded(self, mock_scrappers, mock_selenium):
        SCRAPPERS['Infojobs']['preloaded'] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            runSpecifiedScrappers(['Infojobs'])
        SCRAPPERS['Infojobs']['function'].assert_called()
