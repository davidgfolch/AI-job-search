import pytest
import re
from unittest.mock import MagicMock, patch, call
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from scrapper.navigator.indeedNavigator import (
    IndeedNavigator, 
    CSS_SEL_SEARCH_WHAT, CSS_SEL_SEARCH_WHERE,
    CSS_SEL_SEARCH_BTN, CSS_SEL_NEXT_PAGE_BUTTON, 
    CSS_SEL_SORT_BY_DATE, CSS_SEL_JOB_LINK
)

class TestIndeedNavigator:
    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def mock_authenticator(self):
        with patch('scrapper.navigator.indeedNavigator.IndeedAuthenticator') as mock:
            yield mock.return_value

    @pytest.fixture
    def navigator(self, mock_selenium, mock_authenticator):
        # We need to patch where IndeedAuthenticator is instantiated if we want to check it
        return IndeedNavigator(mock_selenium, False)

    def test_init(self, mock_selenium):
        with patch('scrapper.navigator.indeedNavigator.IndeedAuthenticator') as mock_auth_cls:
            nav = IndeedNavigator(mock_selenium, False)
            mock_auth_cls.assert_called_with(mock_selenium)
            assert nav.authenticator == mock_auth_cls.return_value

    def test_accept_cookies(self, navigator, mock_authenticator):
        navigator.accept_cookies()
        mock_authenticator.accept_cookies.assert_called_once()

    def test_login(self, navigator, mock_authenticator):
        navigator.login()
        mock_authenticator.login.assert_called_once()

    def test_search(self, navigator, mock_selenium):
        with patch('scrapper.navigator.indeedNavigator.sleep'):
            navigator.search("Python", "Remote", True, 7, 1)
            mock_selenium.waitUntil_presenceLocatedElement.assert_called_with(CSS_SEL_SEARCH_WHAT)
            mock_selenium.sendKeys.assert_any_call(CSS_SEL_SEARCH_WHAT, "Python", clear=True)
            mock_selenium.sendKeys.assert_any_call(CSS_SEL_SEARCH_WHERE, "Remote", clear=True)
            mock_selenium.waitAndClick.assert_called_with(CSS_SEL_SEARCH_BTN)

    @pytest.mark.parametrize("elms,expected", [([MagicMock()], True), ([], False)])
    def test_checkNoResults(self, elms, expected, navigator, mock_selenium):
        mock_selenium.getElms.return_value = elms
        with patch.object(IndeedNavigator, 'close_modal'):
            assert navigator.checkNoResults() is expected

    @patch.object(IndeedNavigator, 'selectOption')
    def test_selectFilters(self, mock_select_option, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        navigator.selectFilters(remote=True, daysOld=7)
        assert mock_select_option.call_count == 2

    def test_selectOption(self, navigator, mock_selenium):
        with patch('scrapper.navigator.indeedNavigator.sleep'):
            navigator.selectOption("#btn", "#opt")
            mock_selenium.waitAndClick.assert_any_call("#btn")
            mock_selenium.waitAndClick.assert_any_call("#opt")

    def test_get_total_results(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "1.234 empleos"
        assert navigator.get_total_results("Python") == 1234

    @patch('scrapper.navigator.indeedNavigator.sleep')
    def test_scroll_jobs_list(self, mock_sleep, navigator, mock_selenium):
        mock_li = MagicMock()
        mock_li.is_displayed.return_value = True
        mock_selenium.getElms.return_value = [mock_li]
        assert navigator.scroll_jobs_list(0) is True
        mock_selenium.scrollIntoView.assert_called_with(mock_li)

    @patch.object(IndeedNavigator, 'close_modal')
    @patch('scrapper.navigator.indeedNavigator.sleep')
    def test_click_next_page(self, mock_sleep, mock_close, navigator, mock_selenium):
        assert navigator.click_next_page() is True
        mock_close.assert_called_once()
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON)

    def test_close_modal(self, navigator, mock_selenium):
        mock_btn = MagicMock()
        mock_selenium.getElms.return_value = [mock_btn]
        navigator.close_modal()
        mock_selenium.waitAndClick.assert_called_with(mock_btn)

    def test_get_job_url(self, navigator):
        mock_elm = MagicMock()
        mock_elm.get_attribute.return_value = "https://indeed.com/job?jk=123&cf-turnstile-response=abc"
        with patch('scrapper.navigator.indeedNavigator.baseScrapper.removeUrlParameter', return_value="https://indeed.com/job?jk=123"):
            assert navigator.get_job_url(mock_elm) == "https://indeed.com/job?jk=123"

    def test_get_job_data(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title\n- job post", "Company", "Location"]
        mock_selenium.getHtml.return_value = "<html>Description</html>"
        mock_selenium.getUrl.return_value = "http://job-url"
        t, c, l, u, h = navigator.get_job_data()
        assert t == "Title"
        assert c == "Company"
        assert l == "Location"
        assert u == "http://job-url"
        assert h == "<html>Description</html>"

    def test_clickSortByDate(self, navigator, mock_selenium):
        navigator.clickSortByDate()
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_SORT_BY_DATE)

    def test_scroll_to_bottom(self, navigator, mock_selenium):
        with patch('scrapper.navigator.indeedNavigator.sleep'):
            navigator.scroll_to_bottom()
            mock_selenium.scrollProgressive.assert_any_call(600)
            mock_selenium.scrollProgressive.assert_any_call(-1200)

    def test_load_job_detail(self, navigator, mock_selenium):
        mock_elm = MagicMock()
        navigator.load_job_detail(mock_elm)
        mock_selenium.waitAndClick.assert_called_with(mock_elm)

    def test_get_job_link_element(self, navigator, mock_selenium):
        mock_li = MagicMock()
        mock_link = MagicMock()
        mock_selenium.getElms.return_value = [mock_li]
        mock_selenium.getElmOf.return_value = mock_link
        assert navigator.get_job_link_element(0) == mock_link
        mock_selenium.getElmOf.assert_called_with(mock_li, CSS_SEL_JOB_LINK)

    @pytest.mark.parametrize("elms,expected", [([MagicMock()], True), ([], False)])
    def test_check_easy_apply(self, elms, expected, navigator, mock_selenium):
        mock_selenium.getElms.return_value = elms
        assert navigator.check_easy_apply() is expected
