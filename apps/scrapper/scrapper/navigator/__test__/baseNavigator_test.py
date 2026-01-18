import pytest
from unittest.mock import MagicMock
from scrapper.navigator.baseNavigator import BaseNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class ConcreteNavigator(BaseNavigator):
    def get_total_results(self):
        return 100
    
    def click_next_page(self):
        return True
    
    def scroll_jobs_list(self, idx: int):
        pass
    
    def get_job_data(self):
        return ("title", "company", "location", "url", "description")

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
