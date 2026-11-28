import pytest
from unittest.mock import MagicMock, Mock, patch
from selenium.common.exceptions import TimeoutException
from scrapper.navigator.infojobsNavigator import InfojobsNavigator, CSS_SEL_NEXT_PAGE_BUTTON, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_JOB_DETAIL, SEARCH_URL, OVERLAY_REMOVE_SCRIPT, build_search_url

class TestInfojobsNavigator:

    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def navigator(self, mock_selenium):
        return InfojobsNavigator(mock_selenium, False)

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium

    def test_accept_cookies_undetected(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        navigator.accept_cookies()
        mock_selenium.scrollIntoView_noError.assert_called_with('#didomi-notice-agree-button > span')
        mock_selenium.waitAndClick_noError.assert_called_with('#didomi-notice-agree-button > span', "Accept cookies")

    def test_accept_cookies_normal(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        with patch('scrapper.navigator.infojobsNavigator.sleep') as mock_sleep:
            navigator.accept_cookies()
            assert mock_sleep.call_count > 0
        mock_selenium.scrollIntoView_noError.assert_called_with('#didomi-notice-agree-button > span')
        mock_selenium.waitAndClick_noError.assert_called_with('#didomi-notice-agree-button > span', "Accept cookies")

    def test_security_filter_undetected(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        with patch.object(navigator, 'accept_cookies') as mock_accept:
            navigator.security_filter()
            mock_accept.assert_called_once()
        mock_selenium.waitUntilPageIsLoaded.assert_not_called()

    def test_security_filter_normal(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=False)
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            with patch.object(navigator, 'accept_cookies') as mock_accept:
                navigator.security_filter()
                mock_selenium.waitUntilPageIsLoaded.assert_called()
                assert mock_selenium.waitAndClick.call_count >= 2
                mock_accept.assert_called_once()
                mock_selenium.waitUntilPageUrlContains.assert_called_with('https://www.infojobs.net', 60)

    def test_get_total_results(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "1,234 jobs found"
        result = navigator.get_total_results("python")
        assert result == 1234
        mock_selenium.getText.assert_called_with(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND)

    def test_scroll_to_bottom(self, navigator, mock_selenium):
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            navigator.scroll_to_bottom()
            mock_selenium.scrollProgressive.assert_any_call(600)
            mock_selenium.scrollProgressive.assert_any_call(-1200)

    def test_click_next_page(self, navigator, mock_selenium):
        result = navigator.click_next_page()
        assert result is True
        mock_selenium.driver.execute_script.assert_called_once_with(OVERLAY_REMOVE_SCRIPT)
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON)

    @pytest.mark.parametrize('url', [SEARCH_URL, f'{SEARCH_URL}?keyword=python&page=2'])
    def test_load_search_page_already_loaded(self, navigator, mock_selenium, url):
        mock_selenium.getUrl.return_value = url
        navigator.load_search_page()
        mock_selenium.loadPage.assert_not_called()
        mock_selenium.driver.execute_script.assert_called_once_with(OVERLAY_REMOVE_SCRIPT)

    @pytest.mark.parametrize('url', ['google.com', 'https://www.infojobs.net/', 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'])
    def test_load_search_page_new(self, navigator, mock_selenium, url):
        mock_selenium.getUrl.return_value = url
        navigator.load_search_page()
        mock_selenium.loadPage.assert_called_once_with(SEARCH_URL)
        mock_selenium.waitUntilPageIsLoaded.assert_called_once()
        mock_selenium.driver.execute_script.assert_called_once_with(OVERLAY_REMOVE_SCRIPT)

    @pytest.mark.parametrize('undetected', [True, False])
    def test_security_filter_dismisses_overlays(self, navigator, mock_selenium, undetected):
        mock_selenium.usesUndetectedDriver.return_value = undetected
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            with patch.object(navigator, 'accept_cookies'):
                navigator.security_filter()
        mock_selenium.driver.execute_script.assert_called_once_with(OVERLAY_REMOVE_SCRIPT)

    def test_click_job_link_dismisses_overlays(self, navigator, mock_selenium):
        link = MagicMock()
        navigator.click_job_link(link)
        mock_selenium.driver.execute_script.assert_called_once_with(OVERLAY_REMOVE_SCRIPT)
        mock_selenium.waitAndClick.assert_called_once_with(link)

    def test_wait_for_search_ready_dismisses_overlays(self, navigator):
        with patch.object(navigator, 'dismiss_overlays') as mock_dismiss:
            navigator.waitForSearchReady()
        mock_dismiss.assert_called_once()

    @pytest.mark.parametrize('name', ['last 7 days', 'remote'])
    def test_click_optional_filter_swallows_timeout(self, navigator, mock_selenium, name):
        mock_selenium.waitAndClick.side_effect = TimeoutException('filter not clickable')
        with patch.object(navigator, 'dismiss_overlays') as mock_dismiss:
            navigator.clickOptionalFilter('.ij-SidebarFilter input', name)
        mock_dismiss.assert_called_once()

    @pytest.mark.parametrize('keywords,encoded', [
        ('python', 'python'),
        ('senior software engineer', 'senior%20software%20engineer'),
        ('c# & java', 'c%23%20%26%20java'),
    ])
    def test_build_search_url_encodes_keyword(self, keywords, encoded):
        assert build_search_url(keywords) == f'{SEARCH_URL}?keyword={encoded}'

    @pytest.mark.parametrize('keywords', ['python', 'senior software engineer'])
    def test_load_filtered_search_results_uses_keyword_url(self, navigator, mock_selenium, keywords):
        mock_selenium.getElms.return_value = []
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            assert navigator.load_filtered_search_results(keywords) is True
        mock_selenium.loadPage.assert_called_once_with(build_search_url(keywords))
        mock_selenium.waitUntilPageIsLoaded.assert_called()
        mock_selenium.waitUntil_presenceLocatedElement_noError.assert_called_once_with(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, 10)
        mock_selenium.sendKeys.assert_not_called()
        mock_selenium.sendEscapeKey.assert_not_called()

    @pytest.mark.parametrize('remote_available,expected_dismiss', [(True, 3), (False, 2)])
    def test_date_filter_timeout_does_not_restart_keyword_search(self, navigator, mock_selenium, remote_available, expected_dismiss):
        mock_selenium.getElms.side_effect = lambda selector: ['remote'] if 'check-teleworking' in selector and remote_available else []
        def click(cssSel, **kwargs):
            if '_7_DAYS' in cssSel:
                raise TimeoutException('date filter not clickable')
        mock_selenium.waitAndClick.side_effect = click
        with patch.object(navigator, 'dismiss_overlays') as mock_dismiss:
            with patch('scrapper.navigator.infojobsNavigator.sleep'):
                assert navigator.load_filtered_search_results('Agentic Coding') is True
        assert mock_dismiss.call_count == expected_dismiss
        mock_selenium.loadPage.assert_called_once_with(build_search_url('Agentic Coding'))

    def test_load_filtered_search_results_no_results(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ['some element']
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            assert navigator.load_filtered_search_results('python') is False
        mock_selenium.loadPage.assert_called_once_with(build_search_url('python'))

    def test_scroll_jobs_list(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock(), MagicMock()]
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            navigator.scroll_jobs_list(0)
            mock_selenium.scrollIntoView.assert_called()

    @pytest.mark.parametrize('style, expected', [
        (None, 'border: 5px solid red;'),
        ('color: blue;', 'color: blue;border: 5px solid red;'),
    ])
    def test_scroll_jobs_list_marks_new_cards_without_requiring_style(self, navigator, mock_selenium, style, expected):
        """InfoJobs cards have no style attribute; reading it through getAttr used to exhaust all retries."""
        li = MagicMock()
        li.get_attribute.return_value = style
        mock_selenium.getElms.side_effect = [[], [li], [MagicMock()]]
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            navigator.scroll_jobs_list(0)
        mock_selenium.getAttr.assert_not_called()
        mock_selenium.setAttr.assert_any_call(li, 'style', expected)
        mock_selenium.setAttr.assert_any_call(li, 'style', '')

    def test_get_job_data(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getUrl.return_value = "http://job.url"
        mock_selenium.getHtml.return_value = "<html>"
        
        title, company, location, url, html = navigator.get_job_data()
        
        assert title == "Title"
        assert company == "Company"
        assert location == "Location"
        assert url == "http://job.url"
        assert html == "<html>"
        
        assert mock_selenium.getText.call_count == 3
        mock_selenium.getHtml.assert_called_with(CSS_SEL_JOB_DETAIL)
