import pytest
from unittest.mock import MagicMock, Mock, call, patch
from scrapper.selenium.tecnoempleo_selenium import TecnoempleoNavigator, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_NO_RESULTS, CSS_SEL_PAGINATION_LINKS
from selenium.common.exceptions import NoSuchElementException

class TestTecnoempleoNavigator:

    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def navigator(self, mock_selenium):
        return TecnoempleoNavigator(mock_selenium)

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium

    def test_wait_for_undetected_security_filter(self, navigator, mock_selenium):
        navigator.wait_for_undetected_security_filter()
        mock_selenium.waitUntil_presenceLocatedElement.assert_called_with('#e_mail', 20)

    def test_cloud_flare_security_filter(self, navigator, mock_selenium):
        with patch('scrapper.selenium.tecnoempleo_selenium.sleep'):
            navigator.cloud_flare_security_filter()
            mock_selenium.getElm.assert_called_with('#e_mail')

    def test_login_undetected(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        with patch('scrapper.selenium.tecnoempleo_selenium.sleep'):
             with patch.object(navigator, 'wait_for_undetected_security_filter') as mock_wait:
                navigator.login('user', 'pass')
                mock_wait.assert_called_once()
                mock_selenium.sendKeys.assert_any_call('#e_mail', 'user')
                mock_selenium.sendKeys.assert_any_call('#password', 'pass')

    def test_login_normal(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=False)
        with patch('scrapper.selenium.tecnoempleo_selenium.sleep'):
             with patch.object(navigator, 'cloud_flare_security_filter') as mock_cloud:
                navigator.login('user', 'pass')
                mock_cloud.assert_called_once()
                mock_selenium.sendKeys.assert_any_call('#e_mail', 'user')

    def test_check_results_found(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        result = navigator.check_results("java", "http://url", False)
        assert result is True

    def test_check_results_not_found(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ['element']
        result = navigator.check_results("java", "http://url", False)
        assert result is False

    def test_get_total_results_from_header(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "50 jobs"
        result = navigator.get_total_results_from_header("java", False)
        assert result == 50
        mock_selenium.getText.assert_called_with(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND)

    def test_scroll_to_bottom(self, navigator, mock_selenium):
        navigator.scroll_to_bottom()
        mock_selenium.scrollIntoView.assert_called_with('nav[aria-label=pagination]')

    def test_scroll_jobs_list_retry(self, navigator, mock_selenium):
         navigator.scroll_jobs_list_retry("css")
         mock_selenium.scrollIntoView.assert_called_with("css")

    def test_scroll_jobs_list(self, navigator, mock_selenium):
        with patch.object(navigator, 'scroll_jobs_list_retry') as mock_scroll_retry:
            result = navigator.scroll_jobs_list(1)
            assert result is not None
        mock_selenium.waitUntilClickable.assert_called()

    def test_click_next_page_no_links(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.click_next_page() is False

    def test_click_next_page_numeric_link(self, navigator, mock_selenium):
        mock_element = MagicMock()
        mock_selenium.getElms.return_value = [mock_element]
        mock_selenium.getText.return_value = "5"
        assert navigator.click_next_page() is False

    def test_click_next_page_valid(self, navigator, mock_selenium):
        mock_element = MagicMock()
        mock_selenium.getElms.return_value = [mock_element]
        mock_selenium.getText.return_value = ">"
        assert navigator.click_next_page() is True
        mock_selenium.waitAndClick.assert_called()

    def test_accept_cookies(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ["cookie_button"]
        with patch('scrapper.selenium.tecnoempleo_selenium.sleep'):
             with patch.object(navigator, 'close_create_alert'):
                navigator.accept_cookies()
                mock_selenium.waitAndClick.assert_called()

    def test_close_create_alert(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ["alert_close"]
        navigator.close_create_alert()
        mock_selenium.waitAndClick.assert_called()

    def test_load_detail(self, navigator, mock_selenium):
        assert navigator.load_detail("link_css") is True
        mock_selenium.waitAndClick.assert_called_with("link_css")

    def test_get_job_data(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Data1", "Data2"]
        mock_selenium.getElms.return_value = ["elm1", "elm2"] # for CSS_SEL_JOB_DATA
        mock_selenium.getUrl.return_value = "http://job-url"
        mock_selenium.getHtml.return_value = "<div>Description</div>"
        
        title, company, location, url, html = navigator.get_job_data()
        
        assert title == "Title"
        assert company == "Company"
        assert location == ""
        assert url == "http://job-url"
        assert "Data1" in html
        assert "Data2" in html
        assert "<div>Description</div>" in html

    def test_check_rate_limit(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "You are being rate limited by Cloudflare"
        assert navigator.check_rate_limit() is True

    def test_check_rate_limit_no(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "Everything is fine"
        assert navigator.check_rate_limit() is False
