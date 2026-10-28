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
        mock_selenium.getText.side_effect = ["Title", "Location"]
        mock_selenium.getElms.side_effect = [[MagicMock(text="Company")], []]
        mock_selenium.getUrl.return_value = "https://glassdoor.com/job?jl=123"
        mock_selenium.getHtml.return_value = "<html>Content</html>"
        title, company, location, url, html = navigator.get_job_data()
        assert title == "Title"
        assert company == "Company"
        assert location == "Location"
        assert url == "https://glassdoor.com/job?jl=123"
        assert html == "<html>Content</html>"

    def test_get_job_data_uses_clicked_card_url(self, mock_sleep, navigator, mock_selenium):
        navigator.current_job_url = "https://glassdoor.com/job-listing/x.htm?jl=1010308395629"
        mock_selenium.getText.side_effect = ["Title", "Location"]
        mock_selenium.getElms.side_effect = [[], [MagicMock(text="Company")]]
        assert navigator.get_job_data()[3] == "https://glassdoor.com/job-listing/x.htm?jl=1010308395629"
        mock_selenium.getUrl.assert_not_called()

    def test_get_company_prefers_compact_name(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.side_effect = [[MagicMock(text="Knowmad Mood")], [MagicMock(text="Ignored")]]
        assert navigator.get_company() == "Knowmad Mood"

    def test_get_company_falls_back_to_header_heading(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.side_effect = [[MagicMock(text="")], [MagicMock(text="Airbus")]]
        assert navigator.get_company() == "Airbus"

    def test_get_company_returns_empty_when_no_candidate(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        assert navigator.get_company() == ""

    @pytest.mark.parametrize("url, expected", [
        ("https://www.glassdoor.es/job-listing/x-JV_1.htm?jl=1010308395629", "1010308395629"),
        ("https://www.glassdoor.es/job-listing/x-JV_1.htm?a=1&jobListingId=1009552660667", "1009552660667"),
        ("https://www.glassdoor.es/Empleo/x-empleos-SRCH_IL.0,6.htm", None),
        (None, None),
    ])
    def test_job_id_from_url(self, mock_sleep, url, expected):
        assert GlassdoorNavigator._job_id_from_url(url) == expected

    def test_load_job_detail_opens_pane_and_closes_auth_modal(self, mock_sleep, navigator, mock_selenium):
        li_elm = MagicMock()
        mock_selenium.getAttrOf.return_value = "https://www.glassdoor.es/job-listing/x-JV_1.htm?jl=1010308395629"
        mock_selenium.getElms.return_value = [MagicMock()]
        navigator.load_job_detail(li_elm)
        mock_selenium.waitAndClick.assert_called_once_with(li_elm, scrollIntoView=True)
        mock_selenium.waitUntil_presenceLocatedElement.assert_called_once_with('#jd-job-title-1010308395629')
        mock_selenium.waitAndClick_noError.assert_called_once()
        assert navigator.current_job_url == "https://www.glassdoor.es/job-listing/x-JV_1.htm?jl=1010308395629"

    def test_load_job_detail_without_job_id_in_url(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getAttrOf.return_value = "https://www.glassdoor.es/Empleo/x-empleos-SRCH_IL.0,6.htm"
        mock_selenium.getElms.return_value = []
        navigator.load_job_detail(MagicMock())
        mock_selenium.waitUntil_presenceLocatedElement.assert_not_called()
        mock_selenium.waitAndClick_noError.assert_not_called()

    def test_close_auth_modal_when_absent_does_not_click(self, mock_sleep, navigator, mock_selenium):
        mock_selenium.getElms.return_value = []
        navigator.close_auth_modal()
        mock_selenium.waitAndClick_noError.assert_not_called()
