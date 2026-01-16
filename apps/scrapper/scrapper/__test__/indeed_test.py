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

    @pytest.mark.parametrize("url, expected", [
        ("https://es.indeed.com/viewjob?jk=1234567890&other=param", "1234567890"),
        ("https://es.indeed.com/pagead/clk?mo=r&ad=...&jk=0987654321&...", "0987654321")
    ])
    def test_get_job_id(self, url, expected):
        assert IndeedService(MagicMock(), MagicMock()).get_job_id(url) == expected

    def test_search_jobs_pagination(self):
        with patch("scrapper.indeed.navigator") as mock_nav, \
             patch("scrapper.indeed.service"), \
             patch("scrapper.indeed.load_and_process_row", return_value=True) as mock_row, \
             patch("scrapper.indeed.summarize"), patch("scrapper.indeed.sleep"):
            mock_nav.click_next_page.side_effect = [True, False]
            mock_nav.checkNoResults.return_value = False
            search_jobs("python", startPage=1)
            assert mock_row.call_count == 32

    def test_search_jobs_fast_forward(self):
        with patch("scrapper.indeed.navigator") as mock_nav, \
             patch("scrapper.indeed.service"), \
             patch("scrapper.indeed.load_and_process_row", return_value=True), \
             patch("scrapper.indeed.summarize"), patch("scrapper.indeed.sleep"), \
             patch("scrapper.indeed.baseScrapper.printPage"):
            mock_nav.get_total_results_from_header.return_value = 50
            mock_nav.checkNoResults.return_value = False
            mock_nav.click_next_page.side_effect = [True, True, False]
            search_jobs("python", startPage=3)
            assert mock_nav.click_next_page.call_count == 3

    def test_process_row_insert(self):
        mock_nav = MagicMock(spec=IndeedNavigator)
        mock_svc = MagicMock(spec=IndeedService)
        mock_nav.get_job_data.return_value = ("T", "C", "L", "<h/>")
        mock_nav.check_easy_apply.return_value = False
        mock_svc.process_job.return_value = True
        with patch("scrapper.indeed.navigator", mock_nav), patch("scrapper.indeed.service", mock_svc):
            assert process_row("http://u") is True
            mock_svc.process_job.assert_called_once_with("T", "C", "L", "http://u", "<h/>", False)

    @pytest.mark.parametrize("validate, expected_result, insert_called", [
        (True, True, True),
        (False, False, False)
    ])
    def test_service_process_job(self, validate, expected_result, insert_called):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchOne.return_value = None
        service = IndeedService(mock_mysql, MagicMock())
        service.set_debug(False)
        with patch("scrapper.services.IndeedService.validate", return_value=validate), \
             patch("scrapper.services.IndeedService.htmlToMarkdown", return_value="D"), \
             patch("scrapper.services.IndeedService.mergeDuplicatedJobs"):
            assert service.process_job("T", "C", "L", "http://u?jk=1", "<h/>", False) is expected_result
            if insert_called:
                mock_mysql.insert.assert_called_once()
            else:
                mock_mysql.insert.assert_not_called()

    def test_post_process_markdown(self):
        service = IndeedService(MagicMock(), MagicMock())
        processed = service.post_process_markdown("Check [this](/ofertas-trabajo/123)")
        assert "this" in processed and "/ofertas-trabajo/123" not in processed
