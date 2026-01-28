import pytest
from unittest.mock import patch, MagicMock

class TestSeleniumService:
    def test_initialization(self, selenium_util, mock_driver):
        assert selenium_util.driver == mock_driver

    def test_load_page(self, selenium_util, mock_driver):
        selenium_util.loadPage('https://test.com')
        mock_driver.get.assert_called_with('https://test.com')

    def test_get_url(self, selenium_util, mock_driver):
        mock_driver.current_url = 'https://test.com'
        assert selenium_util.getUrl() == 'https://test.com'

    def test_tab_creation(self, selenium_util, mock_driver):
        mock_driver.current_window_handle = 'new_tab'
        with patch.object(selenium_util.browser_service, 'waitUntilPageIsLoaded'):
            selenium_util.tab('test_tab')
            assert 'test_tab' in selenium_util.tabs

    def test_tab_close(self, selenium_util, mock_driver):
        selenium_util.tabs['test_tab'] = 'handle'
        selenium_util.tabClose('test_tab')
        mock_driver.close.assert_called()
        assert 'test_tab' not in selenium_util.tabs

    @patch('scrapper.services.selenium.browser_service.WebDriverWait')
    def test_wait_until_page_is_loaded(self, mock_wait, selenium_util, mock_driver):
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        selenium_util.waitUntilPageIsLoaded(10)
        mock_wait.assert_called_with(mock_driver, 10)

    @patch('scrapper.core.utils.sleep')
    def test_scroll_progressive_down(self, mock_sleep, selenium_util, mock_driver):
        mock_driver.execute_script.side_effect = [100] + [None] * 20
        selenium_util.scrollProgressive(200)
        assert mock_driver.execute_script.call_count >= 3
        final_call = mock_driver.execute_script.call_args_list[-1]
        assert 'window.scrollTo(0, 300)' in str(final_call)

    @patch('scrapper.core.utils.sleep')
    def test_scroll_progressive_up(self, mock_sleep, selenium_util, mock_driver):
        mock_driver.execute_script.side_effect = [500] + [None] * 20
        selenium_util.scrollProgressive(-200)
        assert mock_driver.execute_script.call_count >= 3
        final_call = mock_driver.execute_script.call_args_list[-1]
        assert 'window.scrollTo(0, 300)' in str(final_call)

    @patch('scrapper.core.utils.sleep')
    def test_scroll_progressive_zero(self, mock_sleep, selenium_util, mock_driver):
        mock_driver.execute_script.side_effect = [100, None]
        selenium_util.scrollProgressive(0)
        final_call = mock_driver.execute_script.call_args_list[-1]
        assert 'window.scrollTo(0, 100)' in str(final_call)

    def test_send_escape_key(self, selenium_util):
        with patch('scrapper.services.selenium.browser_service.webdriver.ActionChains') as mock_action:
            mock_chain = MagicMock()
            mock_action.return_value = mock_chain
            selenium_util.sendEscapeKey()
            mock_chain.send_keys.assert_called()

    def test_back(self, selenium_util, mock_driver):
        selenium_util.back()
        mock_driver.back.assert_called_once()

    def test_exit_driver_alive(self, selenium_util, mock_driver):
        original_quit = mock_driver.quit
        selenium_util.exit()
        original_quit.assert_called()

    def test_tab_close_error_handling(self, selenium_util, mock_driver):
        selenium_util.tabs['test_tab'] = 'handle'
        mock_driver.close.side_effect = Exception('Close error')
        selenium_util.tabClose('test_tab')
        mock_driver.close.side_effect = None
