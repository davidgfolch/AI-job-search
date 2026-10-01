import pytest
from unittest.mock import MagicMock, call, patch
from scrapper.navigator.linkedinNavigator import LinkedinNavigator, CSS_SEL_LOGIN_USER, CSS_SEL_LOGIN_PWD, CSS_SEL_LOGIN_BUTTON, CSS_SEL_LOGIN_BUTTON_LEGACY, CSS_SEL_LOGIN_REMEMBER_ME, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_NO_RESULTS, CSS_SEL_JOB_LINK, CSS_SEL_NEXT_PAGE_BUTTON, CSS_SEL_JOB_FIT_PREFERENCES
from selenium.common.exceptions import NoSuchElementException
TEST_URL = "http://url"

class TestLinkedinNavigator:

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
    @pytest.mark.parametrize("remember_me, checkbox_raises_error", [(True, False), (True, True), (False, False)])
    def test_login(self, mock_sleep, navigator, mock_selenium, remember_me, checkbox_raises_error):
        mock_selenium.getUrl.return_value = 'https://www.linkedin.com/login'
        if checkbox_raises_error:
            mock_selenium.checkboxUnselect.side_effect = Exception("error")
        user_elm, pwd_elm, remember_elm, submit_elm = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        mock_selenium.getElms.side_effect = [[user_elm], [pwd_elm], [remember_elm] if remember_me else [], [], [submit_elm]]
        navigator.login("user", "pass")
        mock_selenium.waitUntil_presenceLocatedElement.assert_any_call(CSS_SEL_LOGIN_USER)
        mock_selenium.waitUntil_presenceLocatedElement.assert_any_call(CSS_SEL_LOGIN_PWD)
        assert mock_selenium.waitUntil_presenceLocatedElement.call_count == 2
        mock_selenium.sendKeys.assert_any_call(user_elm, 'user')
        mock_selenium.sendKeys.assert_any_call(pwd_elm, 'pass')
        if remember_me: # a failing uncheck is warned about but must not abort the login
            mock_selenium.checkboxUnselect.assert_called_with(remember_elm)
        else: # no toggle on the page, or already unchecked
            mock_selenium.checkboxUnselect.assert_not_called()
        mock_selenium.waitAndClick.assert_called_once_with(submit_elm)

    @pytest.mark.parametrize("legacy_elms, button_elms, clicked_from", [
        ([MagicMock()], [], CSS_SEL_LOGIN_BUTTON_LEGACY),  # old linkedin markup
        ([], [MagicMock()], CSS_SEL_LOGIN_BUTTON),  # current markup, submit is the last button of the last form copy
    ])
    def test_loginSubmit(self, navigator, mock_selenium, legacy_elms, button_elms, clicked_from):
        expected_elm = (legacy_elms or button_elms)[-1]
        mock_selenium.getElms.side_effect = [list(legacy_elms), list(button_elms)] # loginSubmit pops from the returned list
        navigator.loginSubmit()
        mock_selenium.getElms.assert_called_with(clicked_from) # resolution stops on the first selector that matches
        mock_selenium.waitAndClick.assert_called_once_with(expected_elm)

    @patch('commonlib.decorator.retry.sleep')
    def test_loginSubmit_not_found(self, mock_retry_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        with pytest.raises(Exception, match='Login submit button not found'):
            navigator.loginSubmit()
        mock_selenium.waitAndClick.assert_not_called()

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

    @pytest.mark.parametrize("current_idx, expected_method", [
        (1, 'getJobInList'),
        (None, 'getJobInList_directUrl'),
    ])
    def test_get_job_data(self, navigator, mock_selenium, current_idx, expected_method):
        navigator.current_idx = current_idx
        with patch.object(navigator, expected_method) as mock_method:
            navigator.get_job_data()
            mock_method.assert_called_once()

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
        mock_selenium.getElms.return_value = [MagicMock()]
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
