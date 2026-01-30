import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.IndeedExecutor import IndeedExecutor
from scrapper.navigator.indeedNavigator import IndeedNavigator
from scrapper.services.IndeedService import IndeedService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    return MagicMock(spec=SeleniumService)

@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.executor.IndeedExecutor.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python')
        yield mock

class TestIndeedExecutor:
    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        # Mocking IndeedNavigator inside IndeedExecutor
        with patch('scrapper.executor.IndeedExecutor.IndeedNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            executor = IndeedExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=True)
            mock_nav.login.assert_called_once()
            mock_nav.search.assert_not_called()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        mock_persistence_manager.get_state.return_value = {}
        with patch('scrapper.executor.IndeedExecutor.IndeedNavigator'), \
             patch('scrapper.executor.IndeedExecutor.IndeedService') as mock_service_cls, \
             patch.object(IndeedExecutor, '_process_keyword') as mock_process_keyword, \
             patch('scrapper.executor.BaseExecutor.MysqlUtil'):
            
            mock_service = mock_service_cls.return_value
            mock_service.should_skip_keyword.return_value = (False, 1)

            executor = IndeedExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=False)
            assert mock_process_keyword.called
            mock_persistence_manager.get_state.assert_called_with("Indeed")
            mock_persistence_manager.finalize_scrapper.assert_called_with("Indeed")

    def test_search_jobs_pagination(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.IndeedExecutor.sleep'), \
             patch.object(IndeedExecutor, '_load_and_process_row', return_value=True) as mock_row, \
             patch('scrapper.executor.IndeedExecutor.IndeedNavigator'):
            
            executor = IndeedExecutor(mock_selenium, mock_persistence_manager, False)
            executor.service = MagicMock()
            mock_nav = executor.navigator
            mock_nav.click_next_page.side_effect = [True, False]
            mock_nav.checkNoResults.return_value = False
            mock_nav.get_total_results.return_value = 50 # to ensure loop runs
            mock_nav.fast_forward_page.return_value = 1

            executor._process_keyword("python", start_page=1)
            # 2 pages * 16 items = 32 calls
            assert mock_row.call_count == 32

    def test_search_jobs_fast_forward(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.IndeedExecutor.sleep'), \
             patch.object(IndeedExecutor, '_load_and_process_row', return_value=True), \
             patch('scrapper.executor.IndeedExecutor.baseScrapper.printPage'), \
             patch('scrapper.executor.IndeedExecutor.IndeedNavigator'):
            
            executor = IndeedExecutor(mock_selenium, mock_persistence_manager, False)
            executor.service = MagicMock()
            mock_nav = executor.navigator
            mock_nav.get_total_results.return_value = 50
            mock_nav.checkNoResults.return_value = False
            # fast_forward_page returns 3. Logic: page = 3-1 = 2.
            # loop: page+=1 -> 3.
            mock_nav.fast_forward_page.return_value = 3
            mock_nav.click_next_page.side_effect = [True, False]
            
            executor._process_keyword("python", start_page=3)
            
            mock_nav.fast_forward_page.assert_called_once_with(3, 50, 16)
            assert mock_nav.click_next_page.call_count == 2

    def test_process_row_insert(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.IndeedExecutor.IndeedNavigator'):
            executor = IndeedExecutor(mock_selenium, mock_persistence_manager, False)
            mock_nav = executor.navigator
            mock_svc = MagicMock(spec=IndeedService)
            executor.service = mock_svc
            
            mock_nav.get_job_data.return_value = ("T", "C", "L", "http://u", "<h/>")
            mock_nav.check_easy_apply.return_value = False
            mock_svc.process_job.return_value = True
            
            assert executor._process_row("http://u") is True
            mock_svc.process_job.assert_called_once_with("T", "C", "L", "http://u", "<h/>", False)

    @pytest.mark.parametrize("url, expected", [
        ("https://es.indeed.com/viewjob?jk=1234567890&other=param", "1234567890"),
        ("https://es.indeed.com/pagead/clk?mo=r&ad=...&jk=0987654321&...", "0987654321")
    ])
    def test_get_job_id(self, url, expected, mock_mysql, mock_persistence_manager):
        assert IndeedService(mock_mysql, mock_persistence_manager, False).get_job_id(url) == expected

    @pytest.mark.parametrize("validate, expected_result, insert_called", [
        (True, True, True),
        (False, False, False)
    ])
    def test_service_process_job(self, validate, expected_result, insert_called, mock_mysql, mock_persistence_manager):
        mock_mysql.fetchOne.return_value = None
        service = IndeedService(mock_mysql, mock_persistence_manager, False)

        with patch("scrapper.services.IndeedService.validate", return_value=validate), \
             patch("scrapper.services.IndeedService.htmlToMarkdown", return_value="D"), \
             patch("scrapper.services.IndeedService.mergeDuplicatedJobs"):
            assert service.process_job("T", "C", "L", "http://u?jk=1", "<h/>", False) is expected_result
            if insert_called:
                mock_mysql.insert.assert_called_once()
            else:
                mock_mysql.insert.assert_not_called()

    def test_post_process_markdown(self, mock_mysql, mock_persistence_manager):
        service = IndeedService(mock_mysql, mock_persistence_manager, False)
        processed = service.post_process_markdown("Check [this](/ofertas-trabajo/123)")
        assert "this" in processed and "/ofertas-trabajo/123" not in processed
