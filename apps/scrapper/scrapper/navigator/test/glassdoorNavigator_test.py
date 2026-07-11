import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.glassdoorNavigator import GlassdoorNavigator
from scrapper.services.selenium.seleniumService import SeleniumService

@patch('scrapper.navigator.glassdoorNavigator.sleep')
class TestGlassdoorNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock(spec=SeleniumService)

    @pytest.fixture
    def navigator(self, mock_selenium):
        return GlassdoorNavigator(mock_selenium, debug=False)

    def test_initialization(self, mock_sleep, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
        assert navigator.authenticator is not None

    def test_check_easy_apply_returns_false(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.check_easy_apply() is False

    def test_check_easy_apply_returns_true(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        assert navigator.check_easy_apply() is True

    def test_check_results_returns_true_when_no_error_element(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.check_results("python", "http://url") is True

    def test_check_results_returns_false_when_error_element_present(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        assert navigator.check_results("clojure", "http://url") is False

    def test_load_main_page(self, mock_sleep, navigator, mock_selenium):
        navigator.load_main_page()
        assert mock_selenium.loadPage.call_count >= 1

    def test_login_delegates_to_authenticator(self, mock_sleep, navigator, mock_selenium):
        with patch.object(navigator.authenticator, 'login') as mock_auth_login:
            navigator.login()
            mock_auth_login.assert_called_once()

    def test_get_job_data(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getUrl.return_value = "https://glassdoor.com/job?jl=123"
        mock_selenium.getHtml.return_value = "<html>Content</html>"
        title, company, location, url, html = navigator.get_job_data()
        assert title == "Title"
        assert company == "Company"
        assert location == "Location"
        assert url == "https://glassdoor.com/job?jl=123"
        assert html == "<html>Content</html>"
