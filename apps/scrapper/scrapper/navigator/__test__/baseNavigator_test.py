import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.baseNavigator import BaseNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

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
        return ConcreteNavigator(mock_selenium)
    
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
    
    def test_get_url(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = "https://example.com"
        assert navigator.get_url() == "https://example.com"
    
    def test_fast_forward_page_logic(self, mock_selenium):
        navigator = ConcreteNavigator(mock_selenium)
        navigator.click_next_page = MagicMock()
        navigator.wait_until_page_is_loaded = MagicMock()
        navigator.click_next_page.side_effect = [True, True, False]
        with patch("scrapper.navigator.baseNavigator.sleep"):
            reached_page = navigator.fast_forward_page(start_page=3, total_results=100, jobs_x_page=10)
        assert reached_page == 3
        assert navigator.click_next_page.call_count == 2
        assert navigator.wait_until_page_is_loaded.call_count == 2
    
    def test_fast_forward_page_stops_if_click_fails(self, mock_selenium):
        navigator = ConcreteNavigator(mock_selenium)
        navigator.click_next_page = MagicMock()
        navigator.wait_until_page_is_loaded = MagicMock()
        navigator.click_next_page.side_effect = [True, False]
        with patch("scrapper.navigator.baseNavigator.sleep"):
            reached_page = navigator.fast_forward_page(start_page=5, total_results=100, jobs_x_page=10)
        assert reached_page == 2
        assert navigator.click_next_page.call_count == 2
    
    def test_fast_forward_page_checks_page_exists(self, mock_selenium):
        navigator = ConcreteNavigator(mock_selenium)
        navigator.click_next_page = MagicMock()
        reached_page = navigator.fast_forward_page(start_page=5, total_results=20, jobs_x_page=10)
        assert reached_page == 1
        navigator.click_next_page.assert_not_called()
