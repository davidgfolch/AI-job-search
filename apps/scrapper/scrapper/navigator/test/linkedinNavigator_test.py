import pytest
from unittest.mock import MagicMock, patch
from scrapper.navigator.linkedinNavigator import LinkedinNavigator, CSS_SEL_LOGIN_USER, CSS_SEL_LOGIN_PWD, CSS_SEL_LOGIN_BUTTON, CSS_SEL_LOGIN_BUTTON_LEGACY, CSS_SEL_LOGIN_REMEMBER_ME, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_JOB_CARD, CSS_SEL_NEXT_PAGE_BUTTON
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
TEST_URL = "http://url"

class TestLinkedinNavigator:

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium
        assert navigator.detail_reader.selenium == mock_selenium

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

    @pytest.mark.parametrize("header_text, header_absent, expected", [
        ('99+ results', False, True),
        ('12 results', False, True),
        ('0 results', False, False),  # empty searches now render a "0 results" header instead of a banner
        (None, True, True),  # header not rendered yet: the loop retries and fails loudly if the layout changed
    ])
    def test_check_results(self, navigator, mock_selenium, header_text, header_absent, expected):
        if header_absent:
            mock_selenium.getText.side_effect = NoSuchElementException('missing')
        else:
            mock_selenium.getText.return_value = header_text
        result = navigator.check_results("key", "url", False, "loc", "tpr")
        assert result is expected

    def test_get_total_results(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "100+ results"
        result = navigator.get_total_results("key", False, "loc", "tpr", "d")
        assert result == 100
        mock_selenium.getText.assert_called_with(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND)

    @pytest.mark.parametrize("idx, expected_pos", [(1, 0), (3, 2)])
    def test_scroll_jobs_list(self, navigator, mock_selenium, idx, expected_pos):
        cards = [MagicMock(), MagicMock(), MagicMock()]
        mock_selenium.getElms.return_value = cards
        elm = navigator.scroll_jobs_list(idx)
        assert elm is cards[expected_pos]
        mock_selenium.getElms.assert_called_with(CSS_SEL_JOB_CARD)
        mock_selenium.scrollIntoView.assert_called_with(cards[expected_pos])
        mock_selenium.moveToElement.assert_called_with(cards[expected_pos])
        mock_selenium.waitUntilClickable.assert_called_with(cards[expected_pos])

    @patch('scrapper.navigator.linkedinNavigator.sleep')
    def test_scroll_jobs_list_not_found(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        with pytest.raises(NoSuchElementException, match='Job card 3'):
            navigator.scroll_jobs_list(3)

    @patch('commonlib.decorator.retry.sleep')
    def test_click_next_page(self, mock_sleep, navigator, mock_selenium):
        assert navigator.click_next_page() is True
        mock_selenium.scrollIntoView.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON)
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON)

    @patch('commonlib.decorator.retry.sleep')
    def test_click_next_page_gives_up_when_intercepted(self, mock_sleep, navigator, mock_selenium):
        # a persistent overlay must not abort the whole run: the loop breaks and the keyword finishes
        mock_selenium.waitAndClick.side_effect = ElementClickInterceptedException('blocked')
        assert navigator.click_next_page() is False
        assert mock_selenium.scrollIntoView.call_count > 1  # re-scrolled on every retry

    def test_load_job_detail_skips_existing(self, navigator, mock_selenium):
        navigator.load_job_detail(True, MagicMock())
        mock_selenium.waitAndClick.assert_not_called()

    def test_load_job_detail_clicks_and_waits(self, navigator, mock_selenium):
        elm = MagicMock()
        mock_selenium.getAttr.return_value = 'job-card-component-ref-42'
        with patch.object(navigator.detail_reader, 'wait_for_job', return_value=True) as wait_for_job:
            navigator.load_job_detail(False, elm)
        mock_selenium.scrollIntoView.assert_called_with(elm)
        mock_selenium.waitAndClick.assert_called_once_with(elm)
        wait_for_job.assert_called_once_with('42')

    def test_load_job_detail_reclicks_on_mismatch(self, navigator, mock_selenium):
        # linkedin overwrites a fresh click with its delayed auto-selection, a re-click must recover
        elm, fresh_elm = MagicMock(), MagicMock()
        mock_selenium.getAttr.return_value = 'job-card-component-ref-42'
        mock_selenium.getElm.return_value = fresh_elm
        with patch.object(navigator.detail_reader, 'wait_for_job', side_effect=[False, True]):
            navigator.load_job_detail(False, elm)
        assert mock_selenium.waitAndClick.call_count == 2
        mock_selenium.waitAndClick.assert_called_with(fresh_elm)

    def test_load_job_detail_retries_intercepted_clicks(self, navigator, mock_selenium):
        elm = MagicMock()
        mock_selenium.getAttr.return_value = 'job-card-component-ref-42'
        mock_selenium.waitAndClick.side_effect = [ElementClickInterceptedException('blocked'), None]
        with patch.object(navigator.detail_reader, 'wait_for_job', return_value=True):
            navigator.load_job_detail(False, elm)
        assert mock_selenium.waitAndClick.call_count == 2
        assert mock_selenium.scrollIntoView.call_count == 2  # re-scrolled before the second attempt

    def test_load_job_detail_raises_when_never_loads(self, navigator, mock_selenium):
        mock_selenium.getAttr.return_value = 'job-card-component-ref-42'
        with patch.object(navigator.detail_reader, 'wait_for_job', return_value=False):
            with pytest.raises(NoSuchElementException, match='never showed job 42'):
                navigator.load_job_detail(False, MagicMock())
        assert mock_selenium.waitAndClick.call_count == 3

    def test_load_job_detail_bad_componentkey(self, navigator, mock_selenium):
        mock_selenium.getAttr.return_value = 'broken-key'
        with pytest.raises(NoSuchElementException, match='No job id'):
            navigator.load_job_detail(False, MagicMock())

    def test_get_job_data(self, navigator, mock_selenium):
        navigator.detail_reader.read = MagicMock(return_value=('T', 'C', 'L', 'U', 'H'))
        assert navigator.get_job_data() == ('T', 'C', 'L', 'U', 'H')

    def test_get_job_url_from_element(self, navigator, mock_selenium):
        mock_selenium.getAttr.return_value = 'job-card-component-ref-123'
        assert navigator.get_job_url_from_element(MagicMock()) == 'https://www.linkedin.com/jobs/view/123/'

    def test_get_job_url_from_element_bad_componentkey(self, navigator, mock_selenium):
        mock_selenium.getAttr.return_value = 'broken-key'
        with pytest.raises(NoSuchElementException, match='No job id'):
            navigator.get_job_url_from_element(MagicMock())

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

    def test_wait_until_page_url_contains(self, navigator, mock_selenium):
        navigator.wait_until_page_url_contains("url", 10)
        mock_selenium.waitUntilPageUrlContains.assert_called_with("url", 10)

    def test_wait_until_page_is_loaded(self, navigator, mock_selenium):
        navigator.wait_until_page_is_loaded()
        mock_selenium.waitUntilPageIsLoaded.assert_called()
