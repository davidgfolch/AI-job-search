import pytest
from unittest.mock import MagicMock, call, patch
from scrapper.navigator.linkedinNavigator import LinkedinNavigator, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_NO_RESULTS, CSS_SEL_JOB_LINK, CSS_SEL_NEXT_PAGE_BUTTON
from selenium.common.exceptions import NoSuchElementException

class TestLinkedinNavigator:

    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def navigator(self, mock_selenium):
        return LinkedinNavigator(mock_selenium)

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium

    def test_load_page(self, navigator, mock_selenium):
        navigator.load_page("http://url")
        mock_selenium.loadPage.assert_called_with("http://url")
        mock_selenium.waitUntilPageIsLoaded.assert_called()

    def test_check_login_popup_present(self, navigator, mock_selenium):
        mock_selenium.waitAndClick_noError.return_value = True
        callback = MagicMock()
        with patch('scrapper.navigator.linkedinNavigator.sleep'):
            result = navigator.check_login_popup(callback)
            assert result is True
            callback.assert_called_once()

    def test_check_login_popup_not_present(self, navigator, mock_selenium):
        mock_selenium.waitAndClick_noError.return_value = False
        callback = MagicMock()
        with patch('scrapper.navigator.linkedinNavigator.sleep'):
            result = navigator.check_login_popup(callback)
            assert result is False
            callback.assert_not_called()

    def test_login_already_logged_in(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.linkedin.com/feed/'
        navigator.login("user", "pass")
        mock_selenium.sendKeys.assert_not_called()

    def test_login_success(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.linkedin.com/login'
        with patch('scrapper.navigator.linkedinNavigator.sleep'):
            navigator.login("user", "pass")
            mock_selenium.sendKeys.assert_any_call('#username', 'user')
            mock_selenium.sendKeys.assert_any_call('#password', 'pass')
            mock_selenium.checkboxUnselect.assert_called_with('div.remember_me__opt_in input')
            mock_selenium.waitAndClick.assert_called_with('form button[type=submit]')

    def test_login_checkbox_fail_handled(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.linkedin.com/login'
        mock_selenium.checkboxUnselect.side_effect = Exception("error")
        with patch('scrapper.navigator.linkedinNavigator.sleep'):
            navigator.login("user", "pass") # Should not crash
            mock_selenium.waitAndClick.assert_called_with('form button[type=submit]')

    def test_check_results_found(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        result = navigator.check_results("key", "url", False, "loc", "tpr")
        assert result is True

    def test_check_results_not_found(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ['element']
        result = navigator.check_results("key", "url", False, "loc", "tpr")
        assert result is False

    def test_get_total_results(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "100+ results"
        result = navigator.get_total_results("key", False, "loc", "tpr")
        assert result == 100
        mock_selenium.getText.assert_called_with(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND)

    def test_scroll_jobs_list_success(self, navigator, mock_selenium):
        navigator.scroll_jobs_list(1)
        mock_selenium.scrollIntoView.assert_called()
        mock_selenium.moveToElement.assert_called()
        mock_selenium.waitUntilClickable.assert_called()

    def test_scroll_jobs_list_retry(self, navigator, mock_selenium):
        mock_selenium.scrollIntoView.side_effect = [NoSuchElementException("err"), None]
        with patch.object(navigator, 'scroll_jobs_list_retry') as mock_retry:
             navigator.scroll_jobs_list(1)
             mock_retry.assert_called_once()
             assert mock_selenium.scrollIntoView.call_count == 2


    def test_click_next_page(self, navigator, mock_selenium):
        result = navigator.click_next_page()
        assert result is True
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)

    def test_load_job_detail_already_exists(self, navigator, mock_selenium):
        navigator.load_job_detail(True, 1, "css")
        mock_selenium.waitAndClick.assert_not_called()

    def test_load_job_detail_idx_1(self, navigator, mock_selenium):
        navigator.load_job_detail(False, 1, "css")
        mock_selenium.waitAndClick.assert_not_called()

    def test_load_job_detail_loading(self, navigator, mock_selenium):
        navigator.load_job_detail(False, 2, "css")
        mock_selenium.waitAndClick.assert_called_with("css")

    def test_get_job_data_in_detail_page(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getUrl.return_value = "http://url"
        mock_selenium.getHtml.return_value = "html"
        
        t, c, l, u, h = navigator.get_job_data_in_detail_page()
        
        assert t == "Title"
        assert c == "Company"
        assert l == "Location"
        assert u == "http://url"
        assert h == "html"
        mock_selenium.waitUntilClickable.assert_called()

    def test_get_job_data_in_list(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getAttr.return_value = "http://url"
        mock_selenium.getHtml.return_value = "html"
        
        t, c, l, u, h = navigator.get_job_data_in_list(0)
        
        assert t == "Title"
        assert c == "Company"
        assert l == "Location"
        assert u == "http://url"
        assert h == "html"
        mock_selenium.getAttr.assert_called()

    def test_check_easy_apply_true(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ["yes"]
        assert navigator.check_easy_apply() is True

    def test_check_easy_apply_false(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.check_easy_apply() is False

    def test_collapse_messages(self, navigator, mock_selenium):
        navigator.collapse_messages()
        mock_selenium.waitAndClick_noError.assert_called()
