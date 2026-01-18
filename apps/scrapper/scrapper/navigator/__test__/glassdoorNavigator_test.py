import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.glassdoorNavigator import GlassdoorNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

class TestGlassdoorNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)
    
    @pytest.fixture
    def navigator(self, mock_selenium):
        return GlassdoorNavigator(mock_selenium)
    
    def test_initialization(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
    
    def test_check_easy_apply_returns_false(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.check_easy_apply() is False
    
    def test_check_easy_apply_returns_true(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        assert navigator.check_easy_apply() is True
    
    def test_load_main_page(self, navigator, mock_selenium):
        navigator.load_main_page()
        assert mock_selenium.loadPage.call_count >= 1
        mock_selenium.waitUntil_presenceLocatedElement.assert_called()
    
    @patch("scrapper.navigator.glassdoorNavigator.sleep")
    def test_login(self, mock_sleep, navigator, mock_selenium):
        with patch.object(navigator, 'load_main_page'):
            navigator.login("user", "pass")
            mock_selenium.sendKeys.assert_any_call('#inlineUserEmail', 'user')
            mock_selenium.sendKeys.assert_any_call('form input#inlineUserPassword', 'pass')
            mock_sleep.assert_called()
    
    def test_get_job_data(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getUrl.return_value = "https://glassdoor.com/job?jl=123"
        mock_selenium.getHtml.return_value = "<html>Content</html>"
        title, company, location, url, html = navigator.get_job_data()
        assert title == "Title"
        assert company == "Company"
        assert location == "Location"
        assert url == "https://glassdoor.com/job?jl=123"
        assert html == "<html>Content</html>"
