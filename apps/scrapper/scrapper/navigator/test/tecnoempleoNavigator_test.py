import pytest
from unittest.mock import MagicMock, Mock, call, patch
from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from scrapper.navigator.tecnoempleoNavigator import TecnoempleoNavigator, CSS_SEL_COMPANY, CSS_JOB_DETAIL_HEADER, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_NO_RESULTS, CSS_SEL_PAGINATION_LINKS, CSS_SEL_JOB_DATA_ITEM, CSS_SEL_JOB_DATA_CAPTION, CSS_SEL_JOB_DATA_VALUE, TOAST_REMOVE_SCRIPT
from selenium.common.exceptions import ElementClickInterceptedException

class TestTecnoempleoNavigator:

    @pytest.fixture
    def mock_selenium(self):
        return MagicMock()

    @pytest.fixture
    def navigator(self, mock_selenium):
        return TecnoempleoNavigator(mock_selenium, False)

    def test_init(self, navigator, mock_selenium):
        assert navigator.selenium == mock_selenium

    def test_wait_for_undetected_security_filter(self, navigator, mock_selenium):
        navigator.wait_for_undetected_security_filter()
        mock_selenium.getElm.assert_called_with('#e_mail')

    def test_cloud_flare_security_filter(self, navigator, mock_selenium):
        with patch('scrapper.navigator.tecnoempleoNavigator.sleep'):
            navigator.cloud_flare_security_filter()
            mock_selenium.getElm.assert_called_with('#e_mail')

    def test_login_undetected(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=True)
        with patch('scrapper.navigator.tecnoempleoNavigator.sleep'):
             with patch.object(navigator, 'wait_for_undetected_security_filter') as mock_wait:
                navigator.login('user', 'pass')
                mock_wait.assert_called_once()
                mock_selenium.sendKeys.assert_any_call('#e_mail', 'user')
                mock_selenium.sendKeys.assert_any_call('#password', 'pass')

    def test_login_normal(self, navigator, mock_selenium):
        mock_selenium.usesUndetectedDriver = Mock(return_value=False)
        with patch('scrapper.navigator.tecnoempleoNavigator.sleep'):
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

    def test_get_total_results(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "50 jobs"
        result = navigator.get_total_results("java", False)
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

    def test_dismiss_toast_clicks_close_button(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ["close"]
        navigator.dismiss_toast()
        mock_selenium.waitAndClick_noError.assert_called_once()

    def test_dismiss_toast_removes_overlay_when_no_button(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        navigator.dismiss_toast()
        mock_selenium.driver.execute_script.assert_called_with(TOAST_REMOVE_SCRIPT)

    def test_click_next_page_dismisses_toast(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        mock_selenium.getText.return_value = ">"
        with patch.object(navigator, 'dismiss_toast') as mock_dismiss:
            assert navigator.click_next_page() is True
        mock_dismiss.assert_called_once()

    def test_click_next_page_retries_when_intercepted(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        mock_selenium.getText.return_value = ">"
        mock_selenium.waitAndClick.side_effect = [ElementClickInterceptedException("toast"), None]
        with patch('commonlib.decorator.retry.sleep'):
            assert navigator.click_next_page() is True
        assert mock_selenium.waitAndClick.call_count == 2

    def test_click_next_page_returns_false_when_always_intercepted(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = [MagicMock()]
        mock_selenium.getText.return_value = ">"
        mock_selenium.waitAndClick.side_effect = ElementClickInterceptedException("toast")
        with patch('commonlib.decorator.retry.sleep'):
            assert navigator.click_next_page() is False

    def test_accept_cookies(self, navigator, mock_selenium):
        mock_selenium.getElms.return_value = ["cookie_button"]
        with patch('scrapper.navigator.tecnoempleoNavigator.sleep'):
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
        mock_selenium.getText.side_effect = ["Title", "Data1", "Data2"]
        mock_selenium.getElms.return_value = ["elm1", "elm2"] # for CSS_SEL_JOB_DATA
        mock_selenium.getUrl.return_value = "http://job-url"
        mock_selenium.getHtml.return_value = "<div>Description</div>"
        with patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoCompanyReader') as mock_company,\
                patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoSalaryReader') as mock_reader:
            mock_company.return_value.read.return_value = "Company"
            mock_reader.return_value.read.return_value = "30.000 € - 36.000 € Bruto/año"
            title, company, location, url, salary, html = navigator.get_job_data()

        assert title == "Title"
        assert company == "Company"
        assert location == ""
        assert url == "http://job-url"
        assert salary == "30.000 € - 36.000 € Bruto/año"
        assert "Data1" in html
        assert "Data2" in html
        assert "<div>Description</div>" in html

    def test_get_job_data_without_salary(self, navigator, mock_selenium):
        """An offer stating no pay range is inserted with salary=None instead of the AI having to infer one"""
        mock_selenium.getText.side_effect = ["Title", "Data1"]
        mock_selenium.getElms.return_value = ["elm1"]
        mock_selenium.getUrl.return_value = "http://job-url"
        mock_selenium.getHtml.return_value = "<div>Description</div>"
        with patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoCompanyReader') as mock_company,\
                patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoSalaryReader') as mock_reader:
            mock_company.return_value.read.return_value = "Company"
            mock_reader.return_value.read.return_value = None
            _, _, _, _, salary, _ = navigator.get_job_data()
        assert salary is None

    def test_get_salary_delegates_to_the_salary_reader(self, navigator, mock_selenium):
        with patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoSalaryReader') as mock_reader:
            mock_reader.return_value.read.return_value = "30.000 €"
            assert navigator.get_salary() == "30.000 €"
        mock_reader.assert_called_once_with(mock_selenium, CSS_SEL_JOB_DATA_ITEM, CSS_SEL_JOB_DATA_CAPTION, CSS_SEL_JOB_DATA_VALUE, False)

    def test_check_rate_limit(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "You are being rate limited by Cloudflare"
        assert navigator.check_rate_limit() is True

    def test_check_rate_limit_no(self, navigator, mock_selenium):
        mock_selenium.getText.return_value = "Everything is fine"
        assert navigator.check_rate_limit() is False

    def test_get_company_delegates_to_the_company_reader(self, navigator, mock_selenium):
        with patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoCompanyReader') as mock_reader:
            mock_reader.return_value.read.return_value = "Sngular"
            assert navigator.get_company() == "Sngular"
        mock_reader.assert_called_once_with(mock_selenium, CSS_SEL_COMPANY, CSS_JOB_DETAIL_HEADER, False)

    def test_get_job_data_company_unspecified(self, navigator, mock_selenium):
        """A job whose offer names no employer at all is still returned, with the unspecified sentinel"""
        mock_selenium.getText.side_effect = ["Title", "Data1"]
        mock_selenium.getElms.return_value = ["elm1"]
        mock_selenium.driver.execute_script.return_value = ''  # no company text node in the header
        mock_selenium.getUrl.return_value = "http://job-url"
        mock_selenium.getHtml.return_value = "<div>Description</div>"
        with patch('scrapper.navigator.tecnoempleoNavigator.TecnoempleoCompanyReader') as mock_company:
            mock_company.return_value.read.return_value = UNSPECIFIED_COMPANY
            title, company, location, url, salary, html = navigator.get_job_data()
        assert title == "Title"
        assert company == UNSPECIFIED_COMPANY
        assert url == "http://job-url"
