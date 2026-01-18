import pytest
from unittest.mock import MagicMock, patch
from scrapper.indeed import run, search_jobs, process_row
from scrapper.navigator.indeedNavigator import IndeedNavigator
from scrapper.services.IndeedService import IndeedService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_deps():
    with patch("scrapper.indeed.IndeedNavigator") as nav, \
         patch("scrapper.indeed.IndeedService") as svc, \
         patch("scrapper.indeed.MysqlUtil") as sql, \
         patch("scrapper.indeed.persistence_manager") as pm:
        yield nav, svc, sql, pm

class TestIndeedScrapper:
    def test_run_preload_page(self):
        mock_selenium = MagicMock(spec=SeleniumService)
        with patch("scrapper.indeed.JOBS_SEARCH", "python"), \
             patch("scrapper.indeed.IndeedNavigator") as mock_nav_class:
            run(mock_selenium, preloadPage=True)
            mock_nav_class.return_value.login.assert_called_once()
            mock_nav_class.return_value.search.assert_not_called()

    def test_run_normal_execution(self):
        mock_sel = MagicMock(spec=SeleniumService)
        mock_pm = MagicMock(spec=PersistenceManager)
        mock_pm.get_state.return_value = {}
        with patch("scrapper.indeed.JOBS_SEARCH", "python"), \
             patch("scrapper.indeed.MysqlUtil"), \
             patch("scrapper.indeed.IndeedNavigator"), \
             patch("scrapper.indeed.IndeedService"), \
             patch("scrapper.indeed.search_jobs") as mock_search:
            run(mock_sel, preloadPage=False, persistenceManager=mock_pm)
            assert mock_search.called
            mock_pm.get_state.assert_called_with("Indeed")
            mock_pm.finalize_scrapper.assert_called_with("Indeed")
    
    def test_search_jobs_pagination(self):
        with patch("scrapper.indeed.navigator") as mock_nav, \
             patch("scrapper.indeed.service"), \
             patch("scrapper.indeed.load_and_process_row", return_value=True) as mock_row, \
             patch("scrapper.indeed.sleep"):
            mock_nav.click_next_page.side_effect = [True, False]
            mock_nav.checkNoResults.return_value = False
            search_jobs("python", startPage=1)
            assert mock_row.call_count == 32
    
    def test_process_row_insert(self):
        mock_nav = MagicMock(spec=IndeedNavigator)
        mock_svc = MagicMock(spec=IndeedService)
        mock_nav.get_job_data.return_value = ("T", "C", "L", "http://u", "<h/>")
        mock_nav.check_easy_apply.return_value = False
        mock_svc.process_job.return_value = True
        with patch("scrapper.indeed.navigator", mock_nav), patch("scrapper.indeed.service", mock_svc):
            assert process_row("http://u") is True
            mock_svc.process_job.assert_called_once_with("T", "C", "L", "http://u", "<h/>", False)
