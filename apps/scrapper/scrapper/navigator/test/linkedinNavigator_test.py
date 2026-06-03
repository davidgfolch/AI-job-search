import pytest
from unittest.mock import MagicMock, call, patch
from scrapper.navigator.linkedinNavigator import LinkedinNavigator, CSS_SEL_LOGIN_USER, CSS_SEL_LOGIN_PWD, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_NO_RESULTS, CSS_SEL_JOB_LINK, CSS_SEL_NEXT_PAGE_BUTTON, CSS_SEL_JOB_FIT_PREFERENCES
from selenium.common.exceptions import NoSuchElementException

TEST_URL = "http://url"


class TestLinkedinNavigator:

    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def navigator(self, mock_selenium):
        return LinkedinNavigator(mock_selenium, False)

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium

    def test_load_page(self, navigator, mock_selenium):
        navigator.load_page(TEST_URL)
        mock_selenium.loadPage.assert_called_with(TEST_URL)
        mock_selenium.waitUntilPageIsLoaded.assert_called()

    @patch('scrapper.navigator.linkedinNavigator.sleep')
    @pytest.mark.parametrize("popup_present", [True, False])
    def test_check_login_popup(self, mock_sleep, navigator, mock_selenium, popup_present):
        mock_selenium.waitAndClick_noError.return_value = popup_present
        callback = MagicMock()
        result = navigator.check_login_popup(callback)
        assert result is popup_present
        if popup_present:
            callback.assert_called_once()
        else:
            callback.assert_not_called()

    def test_login_already_logged_in(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.linkedin.com/feed/'
        navigator.login("user", "pass")
        mock_selenium.sendKeys.assert_not_called()

    @patch('scrapper.navigator.linkedinNavigator.sleep')
    @pytest.mark.parametrize("checkbox_raises_error", [False, True])
    def test_login(self, mock_sleep, navigator, mock_selenium, checkbox_raises_error):
        mock_selenium.getUrl.return_value = 'https://www.linkedin.com/login'
        if checkbox_raises_error:
            mock_selenium.checkboxUnselect.side_effect = Exception("error")
        user_elm = MagicMock()
        pwd_elm = MagicMock()
        btn_elm = MagicMock()
        mock_selenium.getElms.side_effect = [[user_elm], [pwd_elm], [btn_elm]]
        navigator.login("user", "pass")
        if not checkbox_raises_error:
            mock_selenium.sendKeys.assert_any_call(user_elm, 'user')
            mock_selenium.sendKeys.assert_any_call(pwd_elm, 'pass')
            mock_selenium.checkboxUnselect.assert_called_with('div.remember_me__opt_in input')
        mock_selenium.waitAndClick.assert_called_with(btn_elm)

    @pytest.mark.parametrize("getElms_return, expected", [
        ([], True),
        (['element'], False),
    ])
    def test_check_results(self, navigator, mock_selenium, getElms_return, expected):
        mock_selenium.getElms.return_value = getElms_return
        result = navigator.check_results("key", "url", False, "loc", "tpr")
        assert result is expected

    def test_get_total_results(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "100+ results"
        result = navigator.get_total_results("key", False, "loc", "tpr", "d")
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


    def test_scroll_jobs_list_retry_execution(self, navigator, mock_selenium):
        navigator.scroll_jobs_list_retry(1)
        mock_selenium.scrollIntoView.assert_called()
        mock_selenium.moveToElement.assert_called()
        mock_selenium.waitUntilClickable.assert_called()

        result = navigator.click_next_page()
        assert result is True
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)

    @pytest.mark.parametrize("already_exists, idx, should_click", [
        (True, 1, False),
        (False, 1, False),
        (False, 2, True),
    ])
    def test_load_job_detail(self, navigator, mock_selenium, already_exists, idx, should_click):
        navigator.load_job_detail(already_exists, idx, "css")
        if should_click:
            mock_selenium.waitAndClick.assert_called_with("css")
        else:
            mock_selenium.waitAndClick.assert_not_called()



    def test_job_fit_preference_found(self, navigator, mock_selenium):
        # Test fit preference
        mock_selenium.getElms.return_value = ["fit_pref_element"]
        # getText is called for the button, then for title, company, location. 
        # We need to provide enough side effects or valid return values.
        # calls: getText(title_sel) -> "Title", getText(company_sel) -> "Company", getText(location_sel) -> "Location", getText(button) -> "Preference"
        mock_selenium.getText.side_effect = ["Title", "Company", "Location", "Preference"]
        mock_selenium.getAttr.return_value = TEST_URL
        mock_selenium.getHtml.return_value = "job_html"
        
        t, c, l, u, h = navigator.getJobInList(0)
        # fit html will be "Preference", job html is "job_html"
        assert h == "Preferencejob_html"

    def test_getJobInList(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getAttr.return_value = TEST_URL
        mock_selenium.getHtml.return_value = "html"
        
        t, c, l, u, h = navigator.getJobInList(0)
        
        assert t == "Title"
        assert c == "Company"
        assert l == "Location"
        assert u == TEST_URL
        assert h == "html"
        mock_selenium.getAttr.assert_called()

    @pytest.mark.parametrize("getElms_return, expected", [
        (["yes"], True),
        ([], False),
    ])
    def test_check_easy_apply(self, navigator, mock_selenium, getElms_return, expected):
        mock_selenium.getElms.return_value = getElms_return
        assert navigator.check_easy_apply() is expected

    def test_collapse_messages(self, navigator, mock_selenium):
        navigator.collapse_messages()
        mock_selenium.waitAndClick_noError.assert_called()

    def test_getJobInList_directUrl(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getAttr.return_value = TEST_URL
        mock_selenium.getHtml.return_value = "html"
        
        t, c, l, u, h = navigator.getJobInList_directUrl()
        
        assert t == "Title"
        assert c == "Company"
        assert l == "Location"
        assert u == TEST_URL
        assert h == "html"
        mock_selenium.getAttr.assert_called()

    def test_get_job_url_from_element(self, navigator, mock_selenium):
        navigator.get_job_url_from_element("css")
        mock_selenium.getAttr.assert_called_with("css", 'href')

    def test_wait_until_page_url_contains(self, navigator, mock_selenium):
        navigator.wait_until_page_url_contains("url", 10)
        mock_selenium.waitUntilPageUrlContains.assert_called_with("url", 10)

    def test_wait_until_page_is_loaded(self, navigator, mock_selenium):
        navigator.wait_until_page_is_loaded()
        mock_selenium.waitUntilPageIsLoaded.assert_called()
