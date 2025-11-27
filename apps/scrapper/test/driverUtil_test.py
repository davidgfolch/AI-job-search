import pytest
from unittest.mock import MagicMock, patch, Mock
from scrapper.driverUtil import DriverUtil, DESKTOP_USER_AGENTS


class TestDriverUtil:
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_initialization_standard_chrome(self, mock_get_env, mock_chrome):
        """Test initialization with standard Chrome (not undetected)"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        assert driver_util.useUndetected is False
        assert driver_util.driver == mock_driver
        mock_chrome.assert_called_once()
        
        # Verify Chrome options were set
        call_args = mock_chrome.call_args
        assert call_args is not None
        options = call_args.kwargs.get('options')
        assert options is not None
    
    @patch('scrapper.driverUtil.uc.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.isWindowsOS')
    def test_initialization_undetected_chrome_windows(self, mock_is_windows, mock_get_env, mock_uc_chrome):
        """Test initialization with undetected Chrome on Windows"""
        mock_get_env.return_value = True
        mock_is_windows.return_value = True
        mock_driver = MagicMock()
        mock_uc_chrome.return_value = mock_driver
        
        with patch.object(DriverUtil, '_findChrome', return_value='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'):
            driver_util = DriverUtil()
        
        assert driver_util.useUndetected is True
        assert driver_util.driver == mock_driver
        mock_uc_chrome.assert_called_once()
    
    @patch('scrapper.driverUtil.uc.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.isWindowsOS')
    def test_initialization_undetected_chrome_non_windows(self, mock_is_windows, mock_get_env, mock_uc_chrome):
        """Test initialization with undetected Chrome on non-Windows"""
        mock_get_env.return_value = True
        mock_is_windows.return_value = False
        mock_driver = MagicMock()
        mock_uc_chrome.return_value = mock_driver
        
        with patch.object(DriverUtil, '_findChrome', return_value='/usr/bin/google-chrome'):
            driver_util = DriverUtil()
        
        assert driver_util.useUndetected is True
        assert driver_util.driver == mock_driver
        mock_uc_chrome.assert_called_once()
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_initialization_undetected_fallback(self, mock_get_env, mock_chrome):
        """Test fallback to standard Chrome when undetected fails"""
        mock_get_env.return_value = True
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        with patch.object(DriverUtil, '_findChrome', return_value=None):
            driver_util = DriverUtil()
        
        # Should fallback to standard Chrome
        assert driver_util.useUndetected is False
        assert driver_util.driver == mock_driver
        mock_chrome.assert_called_once()
    
    @patch('platform.system')
    @patch('scrapper.driverUtil.os.path.exists')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.webdriver.Chrome')
    def test_findChrome_windows_program_files(self, mock_chrome, mock_get_env, mock_exists, mock_system):
        """Test finding Chrome on Windows in Program Files"""
        mock_system.return_value = 'Windows'
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        def exists_side_effect(path):
            return 'Program Files\\Google\\Chrome' in path or 'Program Files (x86)\\Google\\Chrome' in path
        
        mock_exists.side_effect = exists_side_effect
        
        driver_util = DriverUtil()
        chrome_path = driver_util._findChrome()
        
        assert chrome_path is not None
        assert 'chrome.exe' in chrome_path
    
    @patch('platform.system')
    @patch('scrapper.driverUtil.os.path.exists')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.webdriver.Chrome')
    def test_findChrome_linux(self, mock_chrome, mock_get_env, mock_exists, mock_system):
        """Test finding Chrome on Linux"""
        mock_system.return_value = 'Linux'
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        def exists_side_effect(path):
            return path == '/usr/bin/google-chrome'
        
        mock_exists.side_effect = exists_side_effect
        
        driver_util = DriverUtil()
        chrome_path = driver_util._findChrome()
        
        assert chrome_path == '/usr/bin/google-chrome'
    
    @patch('platform.system')
    @patch('scrapper.driverUtil.os.path.exists')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.webdriver.Chrome')
    def test_findChrome_not_found(self, mock_chrome, mock_get_env, mock_exists, mock_system):
        """Test when Chrome is not found"""
        mock_system.return_value = 'Windows'
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_exists.return_value = False
        
        driver_util = DriverUtil()
        chrome_path = driver_util._findChrome()

        
        assert chrome_path is None
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_apply_stealth_scripts_standard(self, mock_get_env, mock_chrome):
        """Test that stealth scripts are applied for standard Chrome"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        # Verify execute_cdp_cmd was called with stealth script
        assert mock_driver.execute_cdp_cmd.called or mock_driver.execute_script.called
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_apply_stealth_scripts_cdp_failure_fallback(self, mock_get_env, mock_chrome):
        """Test fallback to execute_script when CDP fails"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_driver.execute_cdp_cmd.side_effect = Exception('CDP not supported')
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        # Should fallback to execute_script
        mock_driver.execute_script.assert_called()
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_apply_stealth_scripts_both_fail(self, mock_get_env, mock_chrome):
        """Test when both CDP and execute_script fail"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_driver.execute_cdp_cmd.side_effect = Exception('CDP failed')
        mock_driver.execute_script.side_effect = Exception('Script failed')
        mock_chrome.return_value = mock_driver
        
        # Should not raise exception
        driver_util = DriverUtil()
        assert driver_util.driver == mock_driver
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_isAlive_driver_alive(self, mock_get_env, mock_chrome):
        """Test isAlive returns True when driver is alive"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_driver.current_url = 'https://example.com'
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        assert driver_util.isAlive() is True
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_isAlive_driver_dead(self, mock_get_env, mock_chrome):
        """Test isAlive returns False when driver is dead"""
        from unittest.mock import PropertyMock
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        # Configure current_url property to raise exception
        type(driver_util.driver).current_url = PropertyMock(side_effect=Exception('Driver closed'))
        assert driver_util.isAlive() is False

    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_keepAlive_success(self, mock_get_env, mock_chrome):
        """Test keepAlive executes script successfully"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_driver.execute_script.return_value = 1
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        driver_util.keepAlive()
        
        mock_driver.execute_script.assert_called_with("return 1")
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_keepAlive_failure(self, mock_get_env, mock_chrome):
        """Test keepAlive handles exceptions gracefully"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_driver.execute_script.side_effect = Exception('Script failed')
        mock_chrome.return_value = mock_driver
        
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
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.random.choice')
    def test_random_user_agent_selection(self, mock_choice, mock_get_env, mock_chrome):
        """Test that a random user agent is selected"""
        mock_get_env.return_value = False
        test_user_agent = 'Mozilla/5.0 Test Agent'
        mock_choice.return_value = test_user_agent
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        mock_choice.assert_called_once_with(DESKTOP_USER_AGENTS)
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_chrome_options_configuration(self, mock_get_env, mock_chrome):
        """Test that Chrome options are properly configured"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        # Verify Chrome was called with options
        call_args = mock_chrome.call_args
        assert 'options' in call_args.kwargs
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_page_load_timeout_set(self, mock_get_env, mock_chrome):
        """Test that page load timeout is set for standard Chrome"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        mock_driver.set_page_load_timeout.assert_called_with(180)
        mock_driver.set_script_timeout.assert_called_with(180)
    
    @patch('scrapper.driverUtil.uc.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    @patch('scrapper.driverUtil.isWindowsOS')
    @patch('scrapper.driverUtil.tempfile.mkdtemp')
    def test_undetected_chrome_temp_dir_windows(self, mock_mkdtemp, mock_is_windows, mock_get_env, mock_uc_chrome):
        """Test temporary directory is created for undetected Chrome on Windows"""
        mock_get_env.return_value = True
        mock_is_windows.return_value = True
        mock_mkdtemp.return_value = 'C:\\Temp\\chrome_temp_123'
        mock_driver = MagicMock()
        mock_uc_chrome.return_value = mock_driver
        
        with patch.object(DriverUtil, '_findChrome', return_value='C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'):
            driver_util = DriverUtil()
        
        mock_mkdtemp.assert_called_once()
        assert driver_util.driver == mock_driver
    
    @patch('scrapper.driverUtil.webdriver.Chrome')
    @patch('scrapper.driverUtil.getEnvBool')
    def test_driver_attribute_exists(self, mock_get_env, mock_chrome):
        """Test that driver attribute is set after initialization"""
        mock_get_env.return_value = False
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        driver_util = DriverUtil()
        
        assert hasattr(driver_util, 'driver')
        assert hasattr(driver_util, 'useUndetected')
