import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from scrapper.main import SCRAPPERS, runAllScrappers, runSpecifiedScrappers, timeExpired, validScrapperName, executeScrapperPreload, executeScrapper, runPreload


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
def mock_new_architecture():
    """Mock the new architecture to prevent it from being used in tests"""
    with patch('scrapper.main.NEW_ARCHITECTURE_AVAILABLE', False):
        yield


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
            properties = {'timer': 3600, 'waitBeforeFirstRun': False}
            assert timeExpired('', properties) is True
            assert properties['lastExecution'] == 1000

    def test_first_run_with_wait(self):
        with patch('scrapper.main.getDatetimeNow', return_value=1000):
            properties = {'timer': 3600, 'waitBeforeFirstRun': True}
            assert timeExpired('', properties) is False
            assert properties['lastExecution'] == 1000

    @patch('scrapper.main.getDatetimeNow', side_effect=[100, 1900])
    @patch('scrapper.main.getTimeUnits', return_value='30m 0s')
    def test_not_expired(self, mockGetTimeUnits, mockGetDatetimeNow):
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
    def test_expired(self, mockGetDatetimeNow):
        properties = {
            'timer': 3600,  # 1 hour in seconds
            'waitBeforeFirstRun': False,
            'lastExecution': 100  # Set initial lastExecution
        }
        res = timeExpired('', properties)
        assert res is True
        assert properties['lastExecution'] == 6000  # Should update to new time

    def test_none_last_execution(self):
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


def mockPropertiesFunction(sideEffect=None):
    mockFnc = MagicMock(side_effect=sideEffect)
    return {'function': mockFnc, 'preloaded': None}


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
        properties['function'].assert_called_once_with(mock_selenium, True)
    if runInTabs:
        mock_selenium.tab.assert_called_once_with('')
    assert properties['preloaded'] is preloaded


class TestExecuteScrapper:
    def success(self, mock_selenium):
        properties = mockPropertiesFunction()
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        properties['function'].assert_called_once_with(mock_selenium, False)

    def test_with_tabs(self, mock_selenium):
        properties = mockPropertiesFunction()
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('', properties)
        assert mock_selenium.tab.call_count == 1  # Only the finally block call
        properties['function'].assert_called_once_with(mock_selenium, False)

    def test_with_close_tab(self, mock_selenium):
        properties = mockPropertiesFunction()
        properties['closeTab'] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            executeScrapper('', properties)
        mock_selenium.tabClose.assert_called_once_with('')

    def exception(self, mock_selenium):
        properties = mockPropertiesFunction(Exception("Test error"))
        properties['lastExecution'] = datetime(2025, 1, 1)
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        assert properties['lastExecution'] is None

    def test_keyboard_interrupt(self, mock_selenium):
        properties = mockPropertiesFunction(KeyboardInterrupt())
        with patch('scrapper.main.RUN_IN_TABS', False):
            executeScrapper('', properties)
        properties['function'].assert_called_once()


class TestRunPreload:
    def test_not_preloaded(self, mock_selenium):
        mock_selenium.useUndetected = False
        properties = {}
        assert runPreload(properties) is True

    def test_already_preloaded_no_tabs(self, mock_selenium):
        mock_selenium.useUndetected = False
        properties = {'preloaded': True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            assert runPreload(properties) is False

    def test_with_close_tab(self, mock_selenium):
        mock_selenium.useUndetected = False
        properties = {'preloaded': True, 'closeTab': True}
        with patch('scrapper.main.RUN_IN_TABS', True):
            assert runPreload(properties) is True

    def test_not_in_tabs(self, mock_selenium):
        mock_selenium.useUndetected = False
        properties = {'preloaded': True}
        with patch('scrapper.main.RUN_IN_TABS', False):
            assert runPreload(properties) is True


class TestRunAllScrappers:
    def test_basic(self, mock_scrappers, mock_selenium, reset_scrappers, mock_new_architecture):
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

    def test_with_starting(self, mock_scrappers, mock_selenium, reset_scrappers, mock_new_architecture):
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

    def test_with_tabs(self, mock_scrappers, mock_selenium, reset_scrappers):
        with patch('scrapper.main.consoleTimer'), \
                patch('scrapper.main.getDatetimeNow', return_value=1000), \
                patch('scrapper.main.RUN_IN_TABS', True), \
                patch('scrapper.main.getTimeUnits', return_value='0s'):
            runAllScrappers(waitBeforeFirstRuns=False, starting=False, startingAt=None, loops=1)
        assert mock_selenium.tab.call_count >= 4


class TestRunSpecifiedScrappers:
    def single(self, mock_scrappers, mock_selenium, mock_new_architecture):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 2
        assert SCRAPPERS['Linkedin']['function'].call_count == 0

    def test_multiple(self, mock_scrappers, mock_selenium, mock_new_architecture):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'Linkedin', 'Glassdoor'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 1
        assert SCRAPPERS['Linkedin']['function'].call_count == 1
        assert SCRAPPERS['Glassdoor']['function'].call_count == 1
        assert SCRAPPERS['Indeed']['function'].call_count == 0

    def test_mixed_valid_invalid(self, mock_scrappers, mock_selenium, mock_new_architecture):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['Infojobs', 'InvalidScrapper', 'Linkedin'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 1
        assert SCRAPPERS['Linkedin']['function'].call_count == 1

    def test_case_insensitive(self, mock_scrappers, mock_selenium, mock_new_architecture):
        with patch('scrapper.main.RUN_IN_TABS', False):
            runSpecifiedScrappers(['infojobs', 'LINKEDIN'])
        assert SCRAPPERS['Infojobs']['function'].call_count == 1
        assert SCRAPPERS['Linkedin']['function'].call_count == 1

    def test_with_preloaded(self, mock_scrappers, mock_selenium):
        SCRAPPERS['Infojobs']['preloaded'] = True
        with patch('scrapper.main.RUN_IN_TABS', True):
            runSpecifiedScrappers(['Infojobs'])
        SCRAPPERS['Infojobs']['function'].assert_called()


class TestNewArchitecture:
    """Test new SOLID architecture integration"""
    
    @pytest.fixture
    def mock_container(self):
        with patch('scrapper.main.ScrapperContainer') as mock:
            yield mock
    
    @pytest.fixture
    def mock_scrapping_service(self):
        mock_service = MagicMock()
        mock_service.execute_scrapping.return_value = {
            'total_processed': 5,
            'total_saved': 3,
            'total_duplicates': 2,
            'errors': []
        }
        return mock_service
    
    def test_new_architecture_preload_success(self, mock_selenium, mock_container, mock_scrapping_service):
        """Test new architecture preload success"""
        mock_container.return_value.get_scrapping_service.return_value = mock_scrapping_service
        mock_scrapping_service.execute_scrapping.return_value = {'login_success': True}
        
        properties = {'function': MagicMock()}
        
        with patch('scrapper.main.NEW_ARCHITECTURE_AVAILABLE', True):
            executeScrapperPreload('Linkedin', properties)
        
        mock_scrapping_service.execute_scrapping.assert_called_once_with(
            mock_selenium, [], preload_only=True
        )
        assert properties['preloaded'] is True
    
    def test_new_architecture_preload_failure_fallback(self, mock_selenium, mock_container, mock_scrapping_service):
        """Test new architecture preload failure falls back to old method"""
        mock_container.return_value.get_scrapping_service.return_value = mock_scrapping_service
        mock_scrapping_service.execute_scrapping.return_value = {'login_success': False}
        
        properties = {'function': MagicMock()}
        
        with patch('scrapper.main.NEW_ARCHITECTURE_AVAILABLE', True):
            executeScrapperPreload('Linkedin', properties)
        
        # Should fallback to old method
        properties['function'].assert_called_once_with(mock_selenium, True)
        assert properties['preloaded'] is True
    
    def test_new_architecture_scrapping_success(self, mock_selenium, mock_container, mock_scrapping_service):
        """Test new architecture scrapping execution"""
        mock_container.return_value.get_scrapping_service.return_value = mock_scrapping_service
        
        properties = {'function': MagicMock()}
        
        with patch('scrapper.main.NEW_ARCHITECTURE_AVAILABLE', True), \
             patch('scrapper.main.getEnv', return_value='java,python'):
            executeScrapper('Linkedin', properties)
        
        mock_scrapping_service.execute_scrapping.assert_called_once_with(
            mock_selenium, ['java', 'python'], preload_only=False
        )
    
    def test_new_architecture_scrapping_exception_fallback(self, mock_selenium, mock_container):
        """Test new architecture exception falls back to old method"""
        mock_container.side_effect = Exception("Container error")
        
        properties = {'function': MagicMock()}
        
        with patch('scrapper.main.NEW_ARCHITECTURE_AVAILABLE', True):
            executeScrapper('Linkedin', properties)
        
        # Should fallback to old method
        properties['function'].assert_called_once_with(mock_selenium, False)
    
    def test_non_linkedin_scrapper_uses_old_architecture(self, mock_selenium):
        """Test non-LinkedIn scrappers still use old architecture"""
        properties = {'function': MagicMock()}
        
        with patch('scrapper.main.NEW_ARCHITECTURE_AVAILABLE', True):
            executeScrapperPreload('Infojobs', properties)
            executeScrapper('Infojobs', properties)
        
        # Should use old method for non-LinkedIn scrappers
        assert properties['function'].call_count == 2
        properties['function'].assert_any_call(mock_selenium, True)  # preload
        properties['function'].assert_any_call(mock_selenium, False)  # execute