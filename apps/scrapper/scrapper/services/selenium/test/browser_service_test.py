import pytest
from unittest.mock import MagicMock, patch
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from scrapper.services.selenium import browser_service as browser_service_mod
from scrapper.services.selenium.browser_service import BrowserService
from scrapper.test.log_capture import captured_records

LOG_MODULE = "scrapper.browser_service"


def _events(records, event):
    return [r for r in records if r["event"] == event]


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


class TestGetTitle:
    def test_get_title(self, browser_service, mock_driver):
        mock_driver.title = "Job Title - Indeed.com"
        result = browser_service.getTitle()
        assert result == "Job Title - Indeed.com"


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


class TestSetWindowSize:
    def test_set_window_size(self, browser_service, mock_driver):
        browser_service.set_window_size(500, 600)
        mock_driver.set_window_size.assert_called_once_with(500, 600)

    def test_set_window_size_small(self, browser_service, mock_driver):
        browser_service.set_window_size(300, 400)
        mock_driver.set_window_size.assert_called_once_with(300, 400)


class TestTabLogging:
    def test_logs_default_switch(self, mock_driver):
        service = BrowserService(mock_driver)
        with captured_records(browser_service_mod, LOG_MODULE) as records:
            service.tab()
        switch = _events(records, "tab.switch_default")
        assert len(switch) == 1
        assert switch[0]["tab"] == "window_handle_1"
        assert switch[0]["log_level"] == "info"
        assert "switching to default tab=window_handle_1" in switch[0]["console"]

    def test_logs_existing_switch(self, mock_driver):
        service = BrowserService(mock_driver)
        service.tabs = {"tab1": "handle2"}
        with patch.object(service, 'waitUntilPageIsLoaded'):
            with captured_records(browser_service_mod, LOG_MODULE) as records:
                service.tab("tab1")
        switch = _events(records, "tab.switch_existing")
        assert len(switch) == 1
        assert switch[0]["tab"] == "tab1"

    def test_logs_creation(self, mock_driver):
        service = BrowserService(mock_driver)
        with patch.object(service, 'waitUntilPageIsLoaded'):
            with captured_records(browser_service_mod, LOG_MODULE) as records:
                service.tab("new_tab")
        created = _events(records, "tab.created")
        assert len(created) == 1
        assert created[0]["tab"] == "new_tab"

    @pytest.mark.parametrize("close_error, expected_events", [
        (None, []),
        (RuntimeError("no such window"), ["tab.close_failed"]),
    ], ids=["success", "failure"])
    def test_logs_close_outcome(self, mock_driver, close_error, expected_events):
        mock_driver.close.side_effect = close_error
        service = BrowserService(mock_driver)
        with captured_records(browser_service_mod, LOG_MODULE) as records:
            service.tabClose("tab1")
        assert [r["event"] for r in records] == expected_events
        if expected_events:
            assert records[0]["log_level"] == "error"
            assert records[0]["error"] == "no such window"

    def test_no_record_leaks_page_source(self, mock_driver):
        mock_driver.page_source = "SECRET_PAGE_SOURCE"
        service = BrowserService(mock_driver)
        with captured_records(browser_service_mod, LOG_MODULE) as records:
            service.loadPage("https://example.com")
            service.tab()
        assert "SECRET_PAGE_SOURCE" not in str(records)
