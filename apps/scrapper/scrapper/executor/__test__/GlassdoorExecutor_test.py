import math
import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.GlassdoorExecutor import GlassdoorExecutor
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
    with patch('scrapper.executor.GlassdoorExecutor.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

@pytest.fixture
def mock_get_env():
    with patch('scrapper.executor.GlassdoorExecutor.getEnv') as mock:
        mock.return_value = 'https://www.glassdoor.es/Job/jobs.htm?sc.keyword={search}'
        yield mock

class TestGlassdoorExecutor:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager, mock_get_env):
        with patch('scrapper.executor.GlassdoorExecutor.GlassdoorNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            executor = GlassdoorExecutor(mock_selenium, mock_persistence_manager)
            executor.run(preload_page=True)
            mock_nav.load_main_page.assert_called_once()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        with patch('scrapper.executor.BaseExecutor.MysqlUtil') as mock_mysql_class, \
             patch('scrapper.executor.GlassdoorExecutor.GlassdoorService') as mock_service_class, \
             patch.object(GlassdoorExecutor, '_process_keyword') as mock_process_keyword:
            
            mock_mysql_instance = mock_mysql_class.return_value.__enter__.return_value
            mock_service = mock_service_class.return_value
            mock_service.should_skip_keyword.return_value = (False, 1)
            
            executor = GlassdoorExecutor(mock_selenium, mock_persistence_manager)
            executor.run(preload_page=False)
            
            assert mock_process_keyword.called
            mock_service.prepare_resume.assert_called_once()
            mock_persistence_manager.finalize_scrapper.assert_called_once_with('GLASSDOOR')

    def test_process_keyword(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        with patch.object(GlassdoorExecutor, '_load_and_process_row') as mock_load_and_process, \
             patch('scrapper.executor.GlassdoorExecutor.GlassdoorNavigator') as mock_nav_class:
            
            mock_nav_instance = mock_nav_class.return_value
            executor = GlassdoorExecutor(mock_selenium, mock_persistence_manager)
            # navigator is already mocked via initialization inside Executor using the patched class
            
            executor.navigator.get_total_results.return_value = 5
            executor.navigator.fast_forward_page.return_value = 1
            # JOBS_X_PAGE is 30, so 5 results fit in one page
            
            executor._process_keyword("python", 1)
            
            executor.navigator.load_page.assert_called_once()
            executor.navigator.close_dialogs.assert_called_once()
            assert mock_load_and_process.call_count == 5

    def test_load_and_process_row_exists(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        with patch('scrapper.executor.GlassdoorExecutor.GlassdoorNavigator'):
            executor = GlassdoorExecutor(mock_selenium, mock_persistence_manager)
            mock_nav = executor.navigator
            mock_service = MagicMock()
            executor.service = mock_service
    
            mock_nav.get_job_li_elements.return_value = [MagicMock()]
            mock_nav.get_job_url.return_value = "http://job.url?jl=123"
            mock_service.job_exists_in_db.return_value = ("123", True)
            
            executor._load_and_process_row(0)
            
            mock_service.job_exists_in_db.assert_called_once_with("http://job.url?jl=123")
            mock_service.process_job.assert_not_called()

    def test_load_and_process_row_new_job(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        with patch('scrapper.executor.GlassdoorExecutor.GlassdoorNavigator'):
            executor = GlassdoorExecutor(mock_selenium, mock_persistence_manager)
            mock_nav = executor.navigator
            mock_service = MagicMock()
            executor.service = mock_service
    
            mock_nav.get_job_li_elements.return_value = [MagicMock()]
            mock_nav.get_job_url.return_value = "http://job.url?jl=123"
            mock_service.job_exists_in_db.return_value = ("123", False)
            mock_nav.get_job_data.return_value = ("Title", "Company", "Loc", "URL", "HTML")
            mock_nav.check_easy_apply.return_value = False
            
            executor._load_and_process_row(0)
            
            mock_nav.load_job_detail.assert_called_once()
            mock_service.process_job.assert_called_once_with("Title", "Company", "Loc", "URL", "HTML", False)
            mock_nav.go_back.assert_called_once()

# Navigator and Service tests can remain if they were testing those classes directly,
# but if they were in the same file, I should keep them or move them.
# The original file had TestGlassdoorNavigator and TestGlassdoorService.
# I will keep them here as they are relevant unit tests.

class TestGlassdoorNavigator:
    def test_load_main_page(self, mock_selenium):
        nav = GlassdoorNavigator(mock_selenium)
        nav.load_main_page()
        assert mock_selenium.loadPage.call_count >= 1
        mock_selenium.waitUntil_presenceLocatedElement.assert_called()

    @patch("scrapper.navigator.glassdoorNavigator.sleep")
    def test_login(self, mock_sleep, mock_selenium):
        nav = GlassdoorNavigator(mock_selenium)
        with patch.object(nav, 'load_main_page'):
            nav.login("user", "pass")
            mock_selenium.sendKeys.assert_any_call('#inlineUserEmail', 'user')
            mock_selenium.sendKeys.assert_any_call('form input#inlineUserPassword', 'pass')
            mock_sleep.assert_called()

class TestGlassdoorService:
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.glassdoor.es/job-listing/test?jl=1234567890&other=param", "1234567890"),
        ("https://www.glassdoor.es/job-listing/test?jobListingId=0987654321&other=param", "0987654321"),
    ])
    def test_get_job_id(self, url, expected_id, mock_mysql, mock_persistence_manager):
        service = GlassdoorService(mock_mysql, mock_persistence_manager)
        assert service.get_job_id(url) == expected_id

    def test_process_job(self, mock_mysql, mock_persistence_manager):
        service = GlassdoorService(mock_mysql, mock_persistence_manager)
        
        with patch('scrapper.services.GlassdoorService.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.GlassdoorService.validate', return_value=True), \
             patch('scrapper.services.GlassdoorService.mergeDuplicatedJobs'):
            
            mock_mysql.insert.return_value = 1
            
            result = service.process_job("Title", "Company", "Loc", "http://url?jl=123", "HTML", False)
            
            assert result is True
            mock_mysql.insert.assert_called_once()
