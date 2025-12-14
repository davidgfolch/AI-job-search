import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from scrapper.driverUtil import DriverUtil, DESKTOP_USER_AGENTS
import scrapper.driverUtil as driverUtilModule

class TestDriverUtil:
    
    @pytest.fixture
    def mock_env_bool(self):
        with patch('scrapper.driverUtil.getEnvBool') as mock:
            yield mock

    @pytest.fixture
    def mock_chrome(self):
        with patch('scrapper.driverUtil.webdriver.Chrome') as mock:
            driver = MagicMock()
            mock.return_value = driver
            yield mock

    @pytest.fixture
    def mock_uc_chrome(self):
        with patch('scrapper.driverUtil.uc.Chrome') as mock:
            driver = MagicMock()
            mock.return_value = driver
            yield mock

    @pytest.fixture
    def mock_is_windows(self):
        with patch('scrapper.driverUtil.isWindowsOS') as mock:
            yield mock

    def test_initialization_standard_chrome(self, mock_env_bool, mock_chrome):
        """Test initialization with standard Chrome (not undetected)"""
        mock_env_bool.return_value = False
        
        driver_util = DriverUtil()
        
        assert driver_util.useUndetected is False
        assert driver_util.driver == mock_chrome.return_value
        mock_chrome.assert_called_once()
        
        # Verify Chrome options were set
        call_args = mock_chrome.call_args
        assert call_args is not None
        options = call_args.kwargs.get('options')
        assert options is not None

    @pytest.mark.parametrize("is_windows, chrome_path, expected_path", [
        (True, 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'),
        (False, '/usr/bin/google-chrome', '/usr/bin/google-chrome'),
    ])
    def test_initialization_undetected_chrome(self, mock_env_bool, mock_uc_chrome, mock_is_windows, is_windows, chrome_path, expected_path):
        """Test initialization with undetected Chrome for different OSs"""
        mock_env_bool.return_value = True
        mock_is_windows.return_value = is_windows
        
        with patch.object(DriverUtil, '_findChrome', return_value=chrome_path):
            driver_util = DriverUtil()
        
        assert driver_util.useUndetected is True
        assert driver_util.driver == mock_uc_chrome.return_value
        mock_uc_chrome.assert_called_once()
    
    def test_initialization_undetected_fallback(self, mock_env_bool, mock_chrome):
        """Test fallback to standard Chrome when undetected fails (chrome not found)"""
        mock_env_bool.return_value = True
        
        with patch.object(DriverUtil, '_findChrome', return_value=None):
            driver_util = DriverUtil()
        
        # Should fallback to standard Chrome
        assert driver_util.useUndetected is False
        assert driver_util.driver == mock_chrome.return_value
        mock_chrome.assert_called_once()

    @pytest.mark.parametrize("system_os, paths_exist, expected", [
        ('Windows', lambda p: 'Program Files\\Google\\Chrome' in p, True),
        ('Linux', lambda p: p == '/usr/bin/google-chrome', '/usr/bin/google-chrome'),
        ('Windows', lambda p: False, None) # Not found case
    ])
    def test_findChrome(self, mock_env_bool, mock_chrome, system_os, paths_exist, expected):
        """Test finding Chrome on different OSs and not found scenarios"""
        mock_env_bool.return_value = False
        
        with patch('platform.system', return_value=system_os), \
             patch('scrapper.driverUtil.os.path.exists', side_effect=paths_exist):
            
            driver_util = DriverUtil()
            chrome_path = driver_util._findChrome()
            
            if expected is True: # Check for existence of chrome.exe in path for Windows success
                 assert chrome_path is not None
                 assert 'chrome.exe' in chrome_path
            else:
                 assert chrome_path == expected

    def test_apply_stealth_scripts_standard(self, mock_env_bool, mock_chrome):
        """Test that stealth scripts are applied for standard Chrome"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        
        DriverUtil()
        
        # Verify execute_cdp_cmd was called with stealth script
        assert driver.execute_cdp_cmd.called or driver.execute_script.called

    def test_apply_stealth_scripts_cdp_failure_fallback(self, mock_env_bool, mock_chrome):
        """Test fallback to execute_script when CDP fails"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        driver.execute_cdp_cmd.side_effect = Exception('CDP not supported')
        
        DriverUtil()
        
        # Should fallback to execute_script
        driver.execute_script.assert_called()

    def test_apply_stealth_scripts_both_fail(self, mock_env_bool, mock_chrome):
        """Test when both CDP and execute_script fail"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        driver.execute_cdp_cmd.side_effect = Exception('CDP failed')
        driver.execute_script.side_effect = Exception('Script failed')
        
        # Should not raise exception
        driver_util = DriverUtil()
        assert driver_util.driver == driver

    @pytest.mark.parametrize("is_alive_val, is_alive_result", [
        ('https://example.com', True),
        (Exception('Driver closed'), False)
    ])
    def test_isAlive(self, mock_env_bool, mock_chrome, is_alive_val, is_alive_result):
        """Test isAlive returns correct status based on driver state"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        
        driver_util = DriverUtil()
        
        if isinstance(is_alive_val, Exception):
             type(driver).current_url = PropertyMock(side_effect=is_alive_val)
        else:
             driver.current_url = is_alive_val
             
        assert driver_util.isAlive() is is_alive_result

    def test_keepAlive_success(self, mock_env_bool, mock_chrome):
        """Test keepAlive executes script successfully"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        driver.execute_script.return_value = 1
        
        driver_util = DriverUtil()
        driver_util.keepAlive()
        
        driver.execute_script.assert_called_with("return 1")

    def test_keepAlive_failure(self, mock_env_bool, mock_chrome):
        """Test keepAlive handles exceptions gracefully"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        driver.execute_script.side_effect = Exception('Script failed')
        
        driver_util = DriverUtil()
        # Should not raise exception
        driver_util.keepAlive()

    def test_desktop_user_agents_list(self):
        """Test that DESKTOP_USER_AGENTS is properly populated"""
        assert len(DESKTOP_USER_AGENTS) > 0
        # Check that comments are filtered out
        assert all(not agent.startswith('#') for agent in DESKTOP_USER_AGENTS)
        # Check that empty lines are filtered out
        assert all(len(agent) > 0 for agent in DESKTOP_USER_AGENTS)
        # Check that it contains various browsers
        has_chrome = any('Chrome' in agent for agent in DESKTOP_USER_AGENTS)
        has_firefox = any('Firefox' in agent for agent in DESKTOP_USER_AGENTS)
        assert has_chrome
        assert has_firefox

    @patch('scrapper.driverUtil.random.choice')
    def test_random_user_agent_selection(self, mock_choice, mock_env_bool, mock_chrome):
        """Test that a random user agent is selected"""
        mock_env_bool.return_value = False
        test_user_agent = 'Mozilla/5.0 Test Agent'
        mock_choice.return_value = test_user_agent
        
        DriverUtil()
        
        mock_choice.assert_called_once_with(DESKTOP_USER_AGENTS)

    def test_chrome_options_configuration(self, mock_env_bool, mock_chrome):
        """Test that Chrome options are properly configured"""
        mock_env_bool.return_value = False
        
        DriverUtil()
        
        # Verify Chrome was called with options
        call_args = mock_chrome.call_args
        assert 'options' in call_args.kwargs

    def test_page_load_timeout_set(self, mock_env_bool, mock_chrome):
        """Test that page load timeout is set for standard Chrome"""
        mock_env_bool.return_value = False
        driver = mock_chrome.return_value
        
        DriverUtil()
        
        driver.set_page_load_timeout.assert_called_with(180)
        driver.set_script_timeout.assert_called_with(180)

    @patch('scrapper.driverUtil.tempfile.mkdtemp')
    def test_undetected_chrome_temp_dir_windows(self, mock_mkdtemp, mock_env_bool, mock_is_windows, mock_uc_chrome):
        """Test temporary directory is created for undetected Chrome on Windows"""
        mock_env_bool.return_value = True
        mock_is_windows.return_value = True
        mock_mkdtemp.return_value = 'C:\\Temp\\chrome_temp_123'
        
        with patch.object(DriverUtil, '_findChrome', return_value='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'):
            driver_util = DriverUtil()
        
        mock_mkdtemp.assert_called_once()
        assert driver_util.driver == mock_uc_chrome.return_value

    def test_driver_attribute_exists(self, mock_env_bool, mock_chrome):
        """Test that driver attribute is set after initialization"""
        mock_env_bool.return_value = False
        
        driver_util = DriverUtil()
        
        assert hasattr(driver_util, 'driver')
        assert hasattr(driver_util, 'useUndetected')
