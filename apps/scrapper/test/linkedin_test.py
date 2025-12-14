import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import linkedin
from scrapper.linkedin import run, load_page, search_jobs, process_row, processUrl
from scrapper.services.job_services.linkedin_job_service import LinkedinJobService
from scrapper.selenium.linkedin_selenium import LinkedinNavigator
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    return MagicMock(spec=SeleniumUtil)

@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_navigator():
    return MagicMock(spec=LinkedinNavigator)

@pytest.fixture
def mock_service():
    return MagicMock(spec=LinkedinJobService)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.linkedin.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python')
        yield mock

class TestLinkedinScrapper:

    def test_run_preload_page(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.linkedin.LinkedinNavigator') as MockNavigatorClass, \
             patch('scrapper.linkedin.USER_EMAIL', 'test@email.com'), \
             patch('scrapper.linkedin.USER_PWD', 'password'):
            
            mock_nav_instance = MockNavigatorClass.return_value
            
            run(mock_selenium, preloadPage=True, persistenceManager=mock_persistence_manager)
            
            MockNavigatorClass.assert_called_with(mock_selenium)
            mock_nav_instance.login.assert_called_with('test@email.com', 'password')
            mock_nav_instance.wait_until_page_url_contains.assert_called()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        # Patch MysqlUtil class
        with patch('scrapper.linkedin.MysqlUtil') as mock_mysql_class, \
             patch('scrapper.linkedin.LinkedinNavigator') as MockNavigatorClass, \
             patch('scrapper.linkedin.LinkedinJobService') as MockServiceClass, \
             patch('scrapper.linkedin.process_keyword') as mock_process_keyword, \
             patch('scrapper.linkedin.JOBS_SEARCH', 'python'):
            
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance
            
            mock_service_instance = MockServiceClass.return_value
            mock_service_instance.should_skip_keyword.return_value = (False, 1)

            run(mock_selenium, preloadPage=False, persistenceManager=mock_persistence_manager)

            MockServiceClass.assert_called_with(mock_mysql_instance, mock_persistence_manager)
            mock_service_instance.prepare_resume.assert_called()
            mock_process_keyword.assert_called_with('python', 1)
            mock_service_instance.clear_state.assert_called()

    def test_process_keyword(self):
        with patch('scrapper.linkedin.load_page') as mock_load_page, \
             patch('scrapper.linkedin.search_jobs') as mock_search_jobs:
            
            # Setup global mocks in linkedin module
            mock_navigator = MagicMock()
            mock_navigator.check_login_popup.return_value = False
            mock_navigator.check_results.return_value = True
            
            with patch('scrapper.linkedin.navigator', mock_navigator):
                linkedin.process_keyword('test', 1)
                
                mock_load_page.assert_called_with('test')
                mock_search_jobs.assert_called_with('test', 1)

class TestLinkedinJobService:
    def test_get_job_id(self, mock_mysql, mock_persistence_manager):
        service = LinkedinJobService(mock_mysql, mock_persistence_manager)
        url = "https://www.linkedin.com/jobs/view/1234567890/?other=param"
        assert service.get_job_id(url) == 1234567890

    def test_get_job_url_short(self, mock_mysql, mock_persistence_manager):
        service = LinkedinJobService(mock_mysql, mock_persistence_manager)
        url = "https://www.linkedin.com/jobs/view/1234567890/?other=param"
        expected = "https://www.linkedin.com/jobs/view/1234567890/"
        assert service.get_job_url_short(url) == expected

    def test_process_job_valid(self, mock_mysql, mock_persistence_manager):
        service = LinkedinJobService(mock_mysql, mock_persistence_manager)
        with patch('scrapper.services.job_services.linkedin_job_service.validate', return_value=True), \
             patch('scrapper.services.job_services.linkedin_job_service.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.job_services.linkedin_job_service.mergeDuplicatedJobs'):
             
             mock_mysql.jobExists.return_value = False
             mock_mysql.insert.return_value = 1
             
             service.process_job("Title", "Company", "Loc", "https://www.linkedin.com/jobs/view/123/", "<html>", False, False)
             
             mock_mysql.insert.assert_called_once()

    def test_process_job_invalid(self, mock_mysql, mock_persistence_manager):
        service = LinkedinJobService(mock_mysql, mock_persistence_manager)
        with patch('scrapper.services.job_services.linkedin_job_service.validate', return_value=False), \
             patch('scrapper.services.job_services.linkedin_job_service.htmlToMarkdown', return_value="MD"):
             
             with pytest.raises(ValueError, match="Validation failed"):
                 service.process_job("Title", "Company", "Loc", "https://www.linkedin.com/jobs/view/123/", "<html>", False, False)

class TestLinkedinNavigator:
    def test_get_total_results(self, mock_selenium):
        nav = LinkedinNavigator(mock_selenium)
        mock_selenium.getText.return_value = "100+ items"
        
        total = nav.get_total_results("keyword", "2", "123", "r86400")
        assert total == 100
        mock_selenium.getText.assert_called()
