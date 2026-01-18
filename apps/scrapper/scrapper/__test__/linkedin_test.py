import pytest
from unittest.mock import MagicMock, patch
from scrapper.linkedin import run, search_jobs, process_row, load_and_process_row, _transform_to_search_url
from scrapper.navigator.linkedinNavigator import LinkedinNavigator
from scrapper.services.LinkedinService import LinkedinService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager

class TestLinkedinScrapper:
    def test_run_preload_page(self):
        mock_selenium = MagicMock(spec=SeleniumService)
        mock_pm = MagicMock(spec=PersistenceManager)
        with patch("scrapper.linkedin.JOBS_SEARCH", "python"), \
             patch("scrapper.linkedin.LinkedinNavigator") as mock_nav_class:
            run(mock_selenium, preloadPage=True, persistenceManager=mock_pm)
            mock_nav_class.return_value.login.assert_called_once()
            mock_nav_class.return_value.wait_until_page_url_contains.assert_called_once()
    
    def test_run_normal_execution(self):
        mock_sel = MagicMock(spec=SeleniumService)
        mock_pm = MagicMock(spec=PersistenceManager)
        mock_pm.get_state.return_value = {}
        with patch("scrapper.linkedin.JOBS_SEARCH", "python"), \
             patch("scrapper.linkedin.MysqlUtil"), \
             patch("scrapper.linkedin.LinkedinNavigator"), \
             patch("scrapper.linkedin.LinkedinService") as mock_svc_class, \
             patch("scrapper.linkedin.process_keyword") as mock_process:
            mock_svc_instance = mock_svc_class.return_value
            mock_svc_instance.should_skip_keyword.return_value = (False, 1)
            run(mock_sel, preloadPage=False, persistenceManager=mock_pm)
            assert mock_process.called
            mock_pm.finalize_scrapper.assert_called_with("Linkedin")
    
    @pytest.mark.parametrize("start_page,total_results", [(1, 50), (2, 100)])
    def test_search_jobs_pagination(self, start_page, total_results):
        with patch("scrapper.linkedin.navigator") as mock_nav, \
             patch("scrapper.linkedin.service") as mock_svc, \
             patch("scrapper.linkedin.load_and_process_row", return_value=False) as mock_row, \
             patch("scrapper.linkedin.sleep"):
            mock_nav.get_total_results.return_value = total_results
            mock_nav.fast_forward_page.return_value = start_page
            mock_nav.click_next_page.side_effect = [True, False]
            search_jobs("python", start_page)
            assert mock_row.call_count >= 25
            mock_svc.update_state.assert_called()
    
    def test_process_row(self):
        mock_nav = MagicMock(spec=LinkedinNavigator)
        mock_svc = MagicMock(spec=LinkedinService)
        mock_nav.get_job_data.return_value = ("Title", "Company", "Location", "http://url", "<html/>")
        mock_nav.check_easy_apply.return_value = True
        with patch("scrapper.linkedin.navigator", mock_nav), \
             patch("scrapper.linkedin.service", mock_svc), \
             patch("scrapper.linkedin.sleep"):
            process_row(1)
            mock_svc.process_job.assert_called_once_with("Title", "Company", "Location", "http://url", "<html/>", False, True)
    
    def test_load_and_process_row_existing_job(self):
        with patch("scrapper.linkedin.navigator") as mock_nav, \
             patch("scrapper.linkedin.service") as mock_svc:
            mock_nav.scroll_jobs_list.return_value = MagicMock()
            mock_nav.get_job_url_from_element.return_value = "http://url"
            mock_svc.job_exists_in_db.return_value = ("123", True)
            result = load_and_process_row(1, 0)
            assert result is True
            mock_nav.load_job_detail.assert_called_once_with(True, 1, mock_nav.scroll_jobs_list.return_value)
    
    @pytest.mark.parametrize("input_url,expected_url", [
        ("https://www.linkedin.com/jobs/view/4350893693/", "https://www.linkedin.com/jobs/search/?currentJobId=4350893693"),
        ("https://www.linkedin.com/jobs/search/?currentJobId=123", "https://www.linkedin.com/jobs/search/?currentJobId=123"),
    ])
    def test_transform_to_search_url(self, input_url, expected_url):
        assert _transform_to_search_url(input_url) == expected_url
