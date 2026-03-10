import pytest
from unittest.mock import MagicMock, patch
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from scrapper.services.selenium.browser_service import BrowserService


@pytest.fixture
def mock_driver():
    driver = MagicMock()
    driver.current_window_handle = "window_handle_1"
    driver.current_url = "https://example.com"
    return driver


@pytest.fixture
def browser_service(mock_driver):
    return BrowserService(mock_driver)


class TestBrowserServiceInit:
    def test_init(self, mock_driver, browser_service):
        assert browser_service.driver == mock_driver
        assert browser_service.default_tab == "window_handle_1"
        assert browser_service.tabs == {}


class TestTabClose:
    def test_tab_close_default(self, browser_service, mock_driver):
        browser_service.tabClose()
        mock_driver.close.assert_called_once()

    def test_tab_close_with_name(self, browser_service, mock_driver):
        browser_service.tabs = {"tab1": "handle1"}
        browser_service.tabClose("tab1")
        mock_driver.close.assert_called_once()
        assert "tab1" not in browser_service.tabs


class TestTab:
    def test_tab_switch_to_default(self, browser_service, mock_driver):
        browser_service.tab()
        mock_driver.switch_to.window.assert_called_with("window_handle_1")

    def test_tab_switch_to_existing(self, browser_service, mock_driver):
        browser_service.tabs = {"tab1": "handle2"}
        with patch.object(browser_service, 'waitUntilPageIsLoaded'):
            browser_service.tab("tab1")
        mock_driver.switch_to.window.assert_called_with("handle2")

    def test_tab_create_new(self, browser_service, mock_driver):
        mock_driver.current_window_handle = "new_handle"
        with patch.object(browser_service, 'waitUntilPageIsLoaded'):
            browser_service.tab("new_tab")
        mock_driver.switch_to.new_window.assert_called_with('tab')
        assert browser_service.tabs["new_tab"] == "new_handle"


class TestLoadPage:
    def test_load_page(self, browser_service, mock_driver):
        browser_service.loadPage("https://example.com")
        mock_driver.get.assert_called_once_with("https://example.com")


class TestGetUrl:
    def test_get_url(self, browser_service, mock_driver):
        result = browser_service.getUrl()
        assert result == "https://example.com"


class TestWaitUntilPageUrlContains:
    def test_wait_until_page_url_contains(self, browser_service, mock_driver):
        with patch('scrapper.services.selenium.browser_service.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = True
            browser_service.waitUntilPageUrlContains("example", timeout=15)
            mock_wait.assert_called_once_with(mock_driver, 15)


class TestWaitUntilPageIsLoaded:
    def test_wait_until_page_is_loaded(self, browser_service, mock_driver):
        with patch('scrapper.services.selenium.browser_service.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = True
            browser_service.waitUntilPageIsLoaded(timeout=20)
            mock_wait.assert_called_once_with(mock_driver, 20)


class TestSendEscapeKey:
    def test_send_escape_key(self, browser_service, mock_driver):
        with patch('scrapper.services.selenium.browser_service.webdriver.ActionChains') as mock_action:
            mock_action.return_value.send_keys.return_value.perform.return_value = None
            browser_service.sendEscapeKey()
            mock_action.assert_called_once_with(mock_driver)


class TestScrollProgressive:
    def test_scroll_progressive_positive(self, browser_service, mock_driver):
        mock_driver.execute_script.return_value = 0
        with patch('scrapper.services.selenium.browser_service.sleep'):
            browser_service.scrollProgressive(300)
            assert mock_driver.execute_script.call_count >= 1

    def test_scroll_progressive_negative(self, browser_service, mock_driver):
        mock_driver.execute_script.return_value = 300
        with patch('scrapper.services.selenium.browser_service.sleep'):
            browser_service.scrollProgressive(-300)
            assert mock_driver.execute_script.call_count >= 1


class TestBack:
    def test_back(self, browser_service, mock_driver):
        browser_service.back()
        mock_driver.back.assert_called_once()
