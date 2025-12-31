import pytest
from unittest.mock import MagicMock, Mock, call, patch
from scrapper.navigator.infojobsNavigator import InfojobsNavigator, CSS_SEL_NEXT_PAGE_BUTTON, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND
from selenium.common.exceptions import NoSuchElementException

class TestInfojobsNavigator:

    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def navigator(self, mock_selenium):
        return InfojobsNavigator(mock_selenium)

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium

    def test_accept_cookies_undetected(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        navigator.accept_cookies()
        mock_selenium.scrollIntoView.assert_called_with('#didomi-notice-agree-button > span')
        mock_selenium.waitAndClick.assert_called_with('#didomi-notice-agree-button > span')

    def test_accept_cookies_normal(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        with patch('scrapper.navigator.infojobsNavigator.sleep') as mock_sleep:
            navigator.accept_cookies()
            assert mock_sleep.call_count > 0
        mock_selenium.scrollIntoView.assert_called_with('#didomi-notice-agree-button > span')
        mock_selenium.waitAndClick.assert_called_with('#didomi-notice-agree-button > span')

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

    def test_get_total_results_from_header(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "1,234 jobs found"
        result = navigator.get_total_results_from_header("python")
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
        mock_selenium.waitAndClick.assert_called_with(CSS_SEL_NEXT_PAGE_BUTTON)

    def test_load_search_page_existing(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.infojobs.net/somepath'
        with patch.object(navigator, 'click_on_search_jobs') as mock_click:
            navigator.load_search_page()
            mock_selenium.loadPage.assert_not_called()
            mock_click.assert_called_once()

    def test_load_search_page_new(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'google.com'
        with patch.object(navigator, 'click_on_search_jobs') as mock_click:
            navigator.load_search_page()
            mock_selenium.loadPage.assert_called_with('https://www.infojobs.net/')
            mock_click.assert_called_once()

    def test_click_on_search_jobs_already_there(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.infojobs.net/ofertas-trabajo'
        navigator.click_on_search_jobs()
        mock_selenium.waitAndClick.assert_not_called()

    def test_click_on_search_jobs_navigate(self, navigator, mock_selenium):
        mock_selenium.getUrl.return_value = 'https://www.infojobs.net/'
        navigator.click_on_search_jobs()
        mock_selenium.waitAndClick.assert_called_with('header nav ul li a[href="/ofertas-trabajo"]', scrollIntoView=True)
        mock_selenium.waitUntilPageIsLoaded.assert_called()

    def test_load_filtered_search_results_success(self, navigator, mock_selenium):
        mock_selenium.sendKeys.return_value = True
        mock_selenium.getElms.return_value = [] # No "No results" found
        with patch.object(navigator, 'click_on_search_jobs') as mock_click_search:
             with patch('scrapper.navigator.infojobsNavigator.sleep'):
                result = navigator.load_filtered_search_results("python")
                assert result is True
                mock_click_search.assert_called()
                mock_selenium.sendKeys.assert_called()
                mock_selenium.waitAndClick.assert_called()

    def test_load_filtered_search_results_no_results(self, navigator, mock_selenium):
        mock_selenium.sendKeys.return_value = True
        mock_selenium.getElms.return_value = ['some element'] # "No results" found
        with patch.object(navigator, 'click_on_search_jobs') as mock_click_search:
             with patch('scrapper.navigator.infojobsNavigator.sleep'):
                result = navigator.load_filtered_search_results("python")
                assert result is False

    def test_scroll_jobs_list(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock(), MagicMock()]
        with patch('scrapper.navigator.infojobsNavigator.sleep'):
            navigator.scroll_jobs_list(0)
            mock_selenium.scrollIntoView.assert_called()

    def test_get_job_data(self, navigator, mock_selenium):
        mock_selenium.getText.side_effect = ["Title", "Company", "Location"]
        mock_selenium.getHtml.return_value = "<div>HTML</div>"
        
        title, company, location, html = navigator.get_job_data()
        
        assert title == "Title"
        assert company == "Company"
        assert location == "Location"
        assert html == "<div>HTML</div>"
