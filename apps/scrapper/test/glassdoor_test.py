import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import glassdoor
from scrapper.glassdoor import run, loadMainPage, login, searchJobs, loadAndProcessRow, processRow, getJobId
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    with patch('scrapper.glassdoor.selenium', spec=SeleniumUtil) as mock:
        yield mock

@pytest.fixture
def mock_mysql():
    with patch('scrapper.glassdoor.mysql', spec=MysqlUtil) as mock:
        yield mock

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

    def test_run_preload_page(self, mock_selenium, mock_env_vars):
        mock_selenium_instance = MagicMock(spec=SeleniumUtil)
        
        with patch('scrapper.glassdoor.loadMainPage') as mock_load_main:
            run(mock_selenium_instance, preloadPage=True)
            mock_load_main.assert_called_once()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        mock_selenium_instance = MagicMock(spec=SeleniumUtil)
        
        # Patch MysqlUtil class because run() instantiates it
        with patch('scrapper.glassdoor.MysqlUtil') as mock_mysql_class:
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance
            
            mock_persistence_manager.get_state.return_value = {}
            
            # Mock searchJobs to avoid actual execution loop
            with patch('scrapper.glassdoor.searchJobs') as mock_search_jobs:
                run(mock_selenium_instance, preloadPage=False, persistenceManager=mock_persistence_manager)
                
                assert mock_search_jobs.called
                mock_persistence_manager.get_state.assert_called_with('Glassdoor')
                mock_persistence_manager.clear_state.assert_called_with('Glassdoor')

    def test_load_main_page(self, mock_selenium):
        loadMainPage()
        mock_selenium.loadPage.assert_called_with('https://www.glassdoor.es/index.htm')
        mock_selenium.waitUntil_presenceLocatedElement.assert_called()

    def test_login(self, mock_selenium, mock_env_vars):
        with patch('scrapper.glassdoor.loadMainPage'):
            login()
            mock_selenium.sendKeys.assert_called()
            mock_selenium.waitAndClick.assert_called()
            mock_selenium.waitUntilPageIsLoaded.assert_called()

    def test_get_job_id(self):
        url = "https://www.glassdoor.es/job-listing/test?jl=1234567890&other=param"
        assert getJobId(url) == "1234567890"
        
        url2 = "https://www.glassdoor.es/job-listing/test?jobListingId=0987654321&other=param"
        assert getJobId(url2) == "0987654321"

    def test_search_jobs_pagination(self, mock_selenium, mock_mysql):
        # Setup mocks for searchJobs
        mock_selenium.getText.return_value = "30 jobs" # Total results
        
        with patch('scrapper.glassdoor.getTotalResultsFromHeader', return_value=30), \
             patch('scrapper.glassdoor.clickNextPage') as mock_next_page, \
             patch('scrapper.glassdoor.loadAndProcessRow') as mock_process_row, \
             patch('scrapper.glassdoor.summarize'):
            
            searchJobs("http://test.url/search", startPage=1)
            
            # Should process 30 jobs
            assert mock_process_row.call_count == 30
            # Should not click next page as it fits in one page (30 per page)
            mock_next_page.assert_not_called()

    def test_process_row_insert(self, mock_selenium, mock_mysql):
        # Mock selenium returns for processRow
        mock_selenium.getText.side_effect = ["Job Title", "Company Name", "Location"]
        mock_selenium.getElms.return_value = [MagicMock(text="Company Name")] # For company check
        mock_selenium.getUrl.return_value = "http://job.url?jl=123"
        mock_selenium.getHtml.return_value = "<p>Description</p>"
        
        # Mock validation and mysql
        with patch('scrapper.glassdoor.validate', return_value=True), \
             patch('scrapper.glassdoor.htmlToMarkdown', return_value="Description"), \
             patch('scrapper.glassdoor.mergeDuplicatedJobs'):
            
            mock_mysql.insert.return_value = 1
            
            processRow()
            
            mock_mysql.insert.assert_called_once()
            assert "Job Title" in mock_mysql.insert.call_args[0][0]
            assert "Company Name" in mock_mysql.insert.call_args[0][0]

    def test_process_row_validation_fail(self, mock_selenium, mock_mysql):
        mock_selenium.getText.return_value = "" # Empty title
        mock_selenium.getElms.return_value = []
        
        with patch('scrapper.glassdoor.validate', return_value=False):
            processRow()
            
            mock_mysql.insert.assert_not_called()
