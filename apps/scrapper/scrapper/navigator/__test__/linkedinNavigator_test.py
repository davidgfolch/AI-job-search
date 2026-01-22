import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.linkedinNavigator import LinkedinNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class TestLinkedinNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return LinkedinNavigator(mock_selenium, debug=False)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
    
    @patch("scrapper.navigator.linkedinNavigator.sleep")
    def test_get_total_results(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getText.return_value = "100+ items"
        assert navigator.get_total_results("k", "r", "l", "t", "d") == 100
    
    @patch("scrapper.navigator.linkedinNavigator.sleep")
    def test_get_total_results_exact(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getText.return_value = "50 items"
        assert navigator.get_total_results("k", "r", "l", "t", "d") == 50
    
    def test_check_easy_apply_true(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        assert navigator.check_easy_apply() is True
    
    def test_check_easy_apply_false(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.check_easy_apply() is False
