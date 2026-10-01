import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator import baseNavigator
from scrapper.navigator.baseNavigator import BaseNavigator
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.test.log_capture import captured_records

LOG_MODULE = "scrapper.baseNavigator"

class ConcreteNavigator(BaseNavigator):
    def get_total_results(self, *args, **kwargs) -> int:
        return 0
    def click_next_page(self) -> bool:
        return False
    def scroll_jobs_list(self, idx: int):
        pass
    def get_job_data(self):
        return ("","","","","")

class TestBaseNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return ConcreteNavigator(mock_selenium, debug=False)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
    
    def test_wait_until_page_is_loaded(self, navigator, mock_selenium):
        navigator.wait_until_page_is_loaded()
        mock_selenium.waitUntilPageIsLoaded.assert_called_once()
    
    def test_go_back(self, navigator, mock_selenium):
        navigator.go_back()
        mock_selenium.back.assert_called_once()
    
    def test_load_page(self, navigator, mock_selenium):
        url = "https://example.com"
        navigator.load_page(url)
        mock_selenium.loadPage.assert_called_once_with(url)
        mock_selenium.waitUntilPageIsLoaded.assert_called_once()
    
    @pytest.mark.parametrize("get_url_value,expected", [
        ("https://example.com", "https://example.com"),
    ])
    def test_get_url(self, navigator, mock_selenium, get_url_value, expected):
        mock_selenium.getUrl.return_value = get_url_value
        assert navigator.get_url() == expected
    
    def test_get_url_attribute_not_exists(self, mock_selenium):
        del mock_selenium.getUrl
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        assert navigator.get_url() == ""
    
    def test_fast_forward_page_logic(self, mock_selenium):
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        navigator.click_next_page = MagicMock()
        navigator.wait_until_page_is_loaded = MagicMock()
        navigator.click_next_page.side_effect = [True, True, False]
        with patch("scrapper.navigator.baseNavigator.sleep"):
            reached_page = navigator.fast_forward_page(start_page=3, total_results=100, jobs_x_page=10)
        assert reached_page == 3
        assert navigator.click_next_page.call_count == 2
        assert navigator.wait_until_page_is_loaded.call_count == 2
    
    def test_fast_forward_page_stops_if_click_fails(self, mock_selenium):
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        navigator.click_next_page = MagicMock()
        navigator.wait_until_page_is_loaded = MagicMock()
        navigator.click_next_page.side_effect = [True, False]
        with patch("scrapper.navigator.baseNavigator.sleep"):
            reached_page = navigator.fast_forward_page(start_page=5, total_results=100, jobs_x_page=10)
        assert reached_page == 2
        assert navigator.click_next_page.call_count == 2
    
    def test_fast_forward_page_checks_page_exists(self, mock_selenium):
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        navigator.click_next_page = MagicMock()
        reached_page = navigator.fast_forward_page(start_page=5, total_results=20, jobs_x_page=10)
        assert reached_page == 1
        navigator.click_next_page.assert_not_called()

    def test_close_calls_close_method(self, mock_selenium):
        mock_selenium.close = MagicMock()
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        navigator.close()
        mock_selenium.close.assert_called_once()

    def test_close_does_not_call_exit_method(self, mock_selenium):
        mock_selenium.exit = MagicMock()
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        navigator.close()
        mock_selenium.exit.assert_not_called()


class TestStructuredLogging:
    @pytest.mark.parametrize("url, expected_host, expected_path", [
        ("https://www.linkedin.com/jobs/view/123", "www.linkedin.com", "/jobs/view/123"),
        ("https://es.indeed.com/viewjob?jk=789&sessionid=SECRET", "es.indeed.com", "/viewjob"),
    ], ids=["linkedin", "indeed_with_session_query"])
    def test_load_page_logs_host_and_path_only(self, mock_selenium, url, expected_host, expected_path):
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        with captured_records(baseNavigator, LOG_MODULE) as records:
            navigator.load_page(url)
        assert [r["event"] for r in records] == ["page.loading"]
        assert records[0]["log_level"] == "info"
        assert records[0]["url_host"] == expected_host
        assert records[0]["url_path"] == expected_path
        assert records[0]["console"] == f"Loading page {expected_host}{expected_path}"
        assert "SECRET" not in str(records)
        assert url not in str(records)

    @pytest.mark.parametrize("start_page, total_results, jobs_x_page, expected_event", [
        (3, 100, 10, "page.fast_forwarding"),
        (1, 100, 10, None),
        (5, 20, 10, None),
    ], ids=["fast_forward", "already_first_page", "page_does_not_exist"])
    def test_fast_forward_logging(self, mock_selenium, start_page, total_results, jobs_x_page, expected_event):
        navigator = ConcreteNavigator(mock_selenium, debug=False)
        navigator.click_next_page = MagicMock(return_value=False)
        with patch("scrapper.navigator.baseNavigator.sleep"):
            with captured_records(baseNavigator, LOG_MODULE) as records:
                navigator.fast_forward_page(start_page, total_results, jobs_x_page)
        if expected_event is None:
            assert records == []
        else:
            assert [r["event"] for r in records] == [expected_event]
            assert "Fast forwarding to page 3..." in records[0]["console"]
            assert records[0]["start_page"] == start_page
            assert records[0]["total_results"] == total_results
            assert records[0]["jobs_x_page"] == jobs_x_page
