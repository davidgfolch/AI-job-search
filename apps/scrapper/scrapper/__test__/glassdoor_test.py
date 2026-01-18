import math
import pytest
from unittest.mock import MagicMock, patch
from scrapper.glassdoor import run, process_keyword, load_and_process_row
from scrapper.navigator.glassdoorNavigator import GlassdoorNavigator
from scrapper.services.GlassdoorService import GlassdoorService
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
    with patch('scrapper.glassdoor.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

@pytest.fixture
def mock_get_env():
    with patch('scrapper.glassdoor.getEnv') as mock:
        mock.return_value = 'https://www.glassdoor.es/Job/jobs.htm?sc.keyword={search}'
        yield mock

class TestGlassdoorScrapper:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        with patch('scrapper.glassdoor.GlassdoorNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            run(mock_selenium, preloadPage=True, persistenceManager=mock_persistence_manager)
            mock_nav.load_main_page.assert_called_once()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        with patch('scrapper.glassdoor.MysqlUtil') as mock_mysql_class, \
             patch('scrapper.glassdoor.GlassdoorService') as mock_service_class, \
             patch('scrapper.glassdoor.process_keyword') as mock_process_keyword:
            
            mock_mysql_instance = mock_mysql_class.return_value.__enter__.return_value
            mock_service = mock_service_class.return_value
            mock_service.should_skip_keyword.return_value = (False, 1)
            
            run(mock_selenium, preloadPage=False, persistenceManager=mock_persistence_manager)
            
            assert mock_process_keyword.called
            mock_service.prepare_resume.assert_called_once()
            mock_service.prepare_resume.assert_called_once()
            mock_persistence_manager.finalize_scrapper.assert_called_once_with('GLASSDOOR')

    def test_process_keyword(self, mock_selenium, mock_persistence_manager):
        with patch('scrapper.glassdoor.navigator') as mock_nav, \
             patch('scrapper.glassdoor.service') as mock_service, \
             patch('scrapper.glassdoor.load_and_process_row') as mock_load_and_process:
            
            mock_nav.get_total_results.return_value = 5
            mock_nav.fast_forward_page.return_value = 1
            # JOBS_X_PAGE is 30, so 5 results fit in one page
            
            process_keyword("python", 1)
            
            mock_nav.load_page.assert_called_once()
            mock_nav.close_dialogs.assert_called_once()
            assert mock_load_and_process.call_count == 5

    def test_load_and_process_row_exists(self, mock_selenium):
        with patch('scrapper.glassdoor.navigator') as mock_nav, \
             patch('scrapper.glassdoor.service') as mock_service:
            
            mock_nav.get_job_li_elements.return_value = [MagicMock()]
            mock_nav.get_job_url.return_value = "http://job.url?jl=123"
            mock_service.job_exists_in_db.return_value = ("123", True)
            
            load_and_process_row(0)
            
            mock_service.job_exists_in_db.assert_called_once_with("http://job.url?jl=123")
            mock_service.process_job.assert_not_called()

    def test_load_and_process_row_new_job(self, mock_selenium):
        with patch('scrapper.glassdoor.navigator') as mock_nav, \
             patch('scrapper.glassdoor.service') as mock_service:
            
            mock_nav.get_job_li_elements.return_value = [MagicMock()]
            mock_nav.get_job_url.return_value = "http://job.url?jl=123"
            mock_service.job_exists_in_db.return_value = ("123", False)
            mock_nav.get_job_data.return_value = ("Title", "Company", "Loc", "URL", "HTML")
            mock_nav.check_easy_apply.return_value = False
            
            load_and_process_row(0)
            
            mock_nav.load_job_detail.assert_called_once()
            mock_service.process_job.assert_called_once_with("Title", "Company", "Loc", "URL", "HTML", False)
            mock_nav.go_back.assert_called_once()
