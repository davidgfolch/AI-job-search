import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.IndeedScraplingExecutor import IndeedScraplingExecutor
from scrapper.navigator.indeedScraplingNavigator import IndeedScraplingNavigator
from scrapper.services.IndeedService import IndeedService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.sql.mysqlUtil import MysqlUtil

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
    with patch('scrapper.executor.IndeedScraplingExecutor.getAndCheckEnvVars') as mock, \
         patch('scrapper.executor.IndeedScraplingExecutor.getEnv') as mock_env:
        mock.return_value = ('test@email.com', 'password', 'python')
        mock_env.return_value = "" # No proxies
        yield mock

class TestIndeedScraplingExecutor:
    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        with patch('scrapper.executor.IndeedScraplingExecutor.IndeedScraplingNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            executor = IndeedScraplingExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=True)
            # No login needed for scrapling - it handles Cloudflare automatically
            mock_nav.search.assert_not_called()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        mock_persistence_manager.get_state.return_value = {}
        with patch('scrapper.executor.IndeedScraplingExecutor.IndeedScraplingNavigator'), \
             patch('scrapper.executor.IndeedScraplingExecutor.IndeedService') as mock_service_cls, \
             patch.object(IndeedScraplingExecutor, '_process_keyword') as mock_process_keyword, \
             patch('scrapper.executor.BaseExecutor.MysqlUtil'):
            
            mock_service = mock_service_cls.return_value
            mock_service.should_skip_keyword.return_value = (False, 1)

            executor = IndeedScraplingExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=False)
            assert mock_process_keyword.called
            mock_persistence_manager.get_state.assert_called_with("Indeed")
            mock_persistence_manager.finalize_scrapper.assert_called_with("Indeed")

    def test_search_jobs_pagination(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch.object(IndeedScraplingExecutor, '_load_and_process_row', return_value=True) as mock_row, \
             patch('scrapper.executor.IndeedScraplingExecutor.IndeedScraplingNavigator'):
            
            executor = IndeedScraplingExecutor(mock_selenium, mock_persistence_manager, False)
            executor.service = MagicMock()
            mock_nav = executor.navigator
            mock_nav.click_next_page.side_effect = [True, False]
            mock_nav.checkNoResults.return_value = False
            mock_nav.get_total_results.return_value = 50
            mock_nav.fast_forward_page.return_value = 1
            mock_nav.get_page_job_links.return_value = ["url1", "url2"] * 8 # 16 items

            executor._process_keyword("python", start_page=1)
            # 2 pages * 16 items = 32 calls
            assert mock_row.call_count == 32

    def test_search_jobs_fast_forward(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch.object(IndeedScraplingExecutor, '_load_and_process_row', return_value=True), \
             patch('scrapper.executor.IndeedScraplingExecutor.baseScrapper.printPage'), \
             patch('scrapper.executor.IndeedScraplingExecutor.IndeedScraplingNavigator'):
            
            executor = IndeedScraplingExecutor(mock_selenium, mock_persistence_manager, False)
            executor.service = MagicMock()
            mock_nav = executor.navigator
            mock_nav.get_total_results.return_value = 50
            mock_nav.checkNoResults.return_value = False
            mock_nav.fast_forward_page.return_value = 3
            mock_nav.click_next_page.side_effect = [True, False]
            mock_nav.get_page_job_links.return_value = ["url1"] * 16
            
            executor._process_keyword("python", start_page=3)
            
            mock_nav.fast_forward_page.assert_called_once_with(3, 50, 16)
            assert mock_nav.click_next_page.call_count == 2

    def test_process_row_insert(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.IndeedScraplingExecutor.IndeedScraplingNavigator'):
            executor = IndeedScraplingExecutor(mock_selenium, mock_persistence_manager, False)
            mock_nav = executor.navigator
            mock_svc = MagicMock(spec=IndeedService)
            executor.service = mock_svc
            
            mock_nav.get_job_data.return_value = ("Title", "Company", "Location", "http://u", "<html></html>")
            mock_nav.check_easy_apply.return_value = False
            mock_svc.job_exists_in_db.return_value = (None, False)
            mock_svc.process_job.return_value = True
            
            assert executor._load_and_process_row("http://u") is True
            mock_nav.load_job_detail.assert_called_once_with("http://u")
            
