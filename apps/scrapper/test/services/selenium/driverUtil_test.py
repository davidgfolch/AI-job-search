import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from scrapper.services.selenium.driverUtil import DriverUtil, DESKTOP_USER_AGENTS

@pytest.fixture
def mock_deps():
    with patch('scrapper.services.selenium.driverUtil.getEnvBool') as mock_env, \
         patch('scrapper.services.selenium.driverUtil.webdriver.Chrome') as mock_chrome, \
         patch('scrapper.services.selenium.driverUtil.uc.Chrome') as mock_uc, \
         patch('scrapper.services.selenium.driverUtil.isWindowsOS') as mock_win:
        
        mock_env.return_value = False
        mock_win.return_value = True
        mock_chrome.return_value, mock_uc.return_value = MagicMock(), MagicMock()
        
        yield {'env': mock_env, 'chrome': mock_chrome, 'uc': mock_uc, 'win': mock_win, 
               'c_drv': mock_chrome.return_value, 'uc_drv': mock_uc.return_value}

class TestDriverUtil:
    def test_initialization_standard_chrome(self, mock_deps):
        """Test initialization with standard Chrome"""
        mock_deps['env'].return_value = False
        du = DriverUtil()
        assert du.useUndetected is False
        assert du.driver == mock_deps['c_drv']
        mock_deps['chrome'].assert_called_once()
        assert mock_deps['chrome'].call_args.kwargs.get('options') is not None

    @pytest.mark.parametrize("is_win, path", [(True, 'C:\\Chrome\\chrome.exe'), (False, '/usr/bin/google-chrome')])
    def test_initialization_undetected_chrome(self, mock_deps, is_win, path):
        """Test initialization with undetected Chrome"""
        mock_deps['env'].return_value = True
        mock_deps['win'].return_value = is_win
        with patch.object(DriverUtil, '_findChrome', return_value=path):
            du = DriverUtil()
        assert du.useUndetected is True
        assert du.driver == mock_deps['uc_drv']
        mock_deps['uc'].assert_called_once()
    
    def test_initialization_undetected_fallback(self, mock_deps):
        """Test fallback when undetected fails"""
        mock_deps['env'].return_value = True
        with patch.object(DriverUtil, '_findChrome', return_value=None):
            du = DriverUtil()
        assert du.useUndetected is False
        assert du.driver == mock_deps['c_drv']

    @pytest.mark.parametrize("os_name, exists_cb, expected", [
        ('Windows', lambda p: 'Chrome' in p, True),
        ('Linux', lambda p: p == '/usr/bin/google-chrome', '/usr/bin/google-chrome'), 
        ('Windows', lambda p: False, None)
    ])
    def test_findChrome(self, mock_deps, os_name, exists_cb, expected):
        """Test finding Chrome path"""
        with patch('platform.system', return_value=os_name), \
             patch('scrapper.services.selenium.driverUtil.os.path.exists', side_effect=exists_cb):
            mock_deps['env'].return_value = False
            path = DriverUtil()._findChrome()
            assert ('chrome.exe' in path) if expected is True else (path == expected)

    @pytest.mark.parametrize("cdp_err, scr_err, expect_fallback", [
        (None, None, False), (Exception('CDP'), None, True), (Exception('CDP'), Exception('Script'), True)
    ])
    def test_apply_stealth_scripts(self, mock_deps, cdp_err, scr_err, expect_fallback):
        """Test stealth script application failures"""
        mock_deps['env'].return_value = False
        drv = mock_deps['c_drv']
        if cdp_err: drv.execute_cdp_cmd.side_effect = cdp_err
        if scr_err: drv.execute_script.side_effect = scr_err
        DriverUtil()
        if not cdp_err: assert drv.execute_cdp_cmd.called or drv.execute_script.called
        if expect_fallback: assert drv.execute_script.called

    @pytest.mark.parametrize("url_se, expected", [('https://a.com', True), (Exception('Closed'), False)])
    def test_isAlive(self, mock_deps, url_se, expected):
        """Test isAlive status"""
        mock_deps['env'].return_value = False
        drv = mock_deps['c_drv']
        if isinstance(url_se, Exception): type(drv).current_url = PropertyMock(side_effect=url_se)
        else: drv.current_url = url_se
        assert DriverUtil().isAlive() is expected

    @pytest.mark.parametrize("script_se", [1, Exception('Fail')])
    def test_keepAlive(self, mock_deps, script_se):
        """Test keepAlive execution"""
        mock_deps['env'].return_value = False
        drv = mock_deps['c_drv']
        if isinstance(script_se, Exception): drv.execute_script.side_effect = script_se
        else: drv.execute_script.return_value = script_se
        DriverUtil().keepAlive()
        if not isinstance(script_se, Exception): drv.execute_script.assert_called_with("return 1")

    def test_desktop_user_agents_list(self):
        """Test USER_AGENTS validity"""
        assert len(DESKTOP_USER_AGENTS) > 0
        assert all(not a.startswith('#') and len(a) > 0 for a in DESKTOP_USER_AGENTS)
        assert any('Chrome' in a for a in DESKTOP_USER_AGENTS) and any('Firefox' in a for a in DESKTOP_USER_AGENTS)

    @patch('scrapper.services.selenium.driverUtil.random.choice')
    def test_random_user_agent_selection(self, mock_choice, mock_deps):
        """Test random UA selection"""
        mock_deps['env'].return_value = False
        mock_choice.return_value = 'Test Agent'
        DriverUtil()
        mock_choice.assert_called_once_with(DESKTOP_USER_AGENTS)

    def test_chrome_options_configuration(self, mock_deps):
        """Test Chrome options"""
        mock_deps['env'].return_value = False
        DriverUtil()
        assert 'options' in mock_deps['chrome'].call_args.kwargs
        mock_deps['c_drv'].set_page_load_timeout.assert_called_with(180)

    @patch('scrapper.services.selenium.driverUtil.tempfile.mkdtemp')
    def test_undetected_chrome_temp_dir_windows(self, mock_mkdtemp, mock_deps):
        """Test temp dir for undetected Chrome"""
        mock_deps['env'].return_value = True
        mock_deps['win'].return_value = True
        mock_mkdtemp.return_value = 'C:\\Temp'
        with patch.object(DriverUtil, '_findChrome', return_value='C:\\Chrome'):
            du = DriverUtil()
        mock_mkdtemp.assert_called_once()
        assert du.driver == mock_deps['uc_drv']

    def test_driver_attribute_exists(self, mock_deps):
        mock_deps['env'].return_value = False
        du = DriverUtil()
        assert hasattr(du, 'driver') and hasattr(du, 'useUndetected')
