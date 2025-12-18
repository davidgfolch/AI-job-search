import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import glassdoor
from scrapper.glassdoor import run, loadMainPage, login, searchJobs, loadAndProcessRow, processRow, getJobId
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    with patch('scrapper.glassdoor.selenium', spec=SeleniumService) as mock:
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

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        mock_selenium_instance = MagicMock(spec=SeleniumService)
        
        with patch('scrapper.glassdoor.loadMainPage') as mock_load_main:
            run(mock_selenium_instance, preloadPage=True, persistenceManager=mock_persistence_manager)
            mock_load_main.assert_called_once()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_get_env):
        mock_selenium_instance = MagicMock(spec=SeleniumService)
        
        # Patch MysqlUtil class because run() instantiates it
        with patch('scrapper.glassdoor.MysqlUtil') as mock_mysql_class:
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance
            
            mock_persistence_manager.get_state.return_value = {}
            mock_persistence_manager.should_skip_keyword.return_value = (False, 1)
            
            # Mock searchJobs to avoid actual execution loop
            with patch('scrapper.glassdoor.searchJobs') as mock_search_jobs:
                run(mock_selenium_instance, preloadPage=False, persistenceManager=mock_persistence_manager)
                
                assert mock_search_jobs.called
                mock_persistence_manager.prepare_resume.assert_called_with('Glassdoor')
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

    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.glassdoor.es/job-listing/test?jl=1234567890&other=param", "1234567890"),
        ("https://www.glassdoor.es/job-listing/test?jobListingId=0987654321&other=param", "0987654321"),
        ("https://www.glassdoor.es/job-listing/test?jl=11111", "11111"),
        ("https://www.glassdoor.es/job-listing/test?jobListingId=22222", "22222"),
    ])
    def test_get_job_id(self, url, expected_id):
        assert getJobId(url) == expected_id

    def test_search_jobs_pagination(self, mock_selenium, mock_mysql, mock_persistence_manager):
        # Setup mocks for searchJobs
        mock_selenium.getText.return_value = "30 jobs" # Total results
        
        with patch('scrapper.glassdoor.getTotalResultsFromHeader', return_value=30), \
             patch('scrapper.glassdoor.clickNextPage') as mock_next_page, \
             patch('scrapper.glassdoor.loadAndProcessRow') as mock_process_row, \
             patch('scrapper.glassdoor.summarize'):
            
            searchJobs("http://test.url/search", startPage=1, persistenceManager=mock_persistence_manager)
            
            # Should process 30 jobs
            assert mock_process_row.call_count == 30
            # Should not click next page as it fits in one page (30 per page)
            mock_next_page.assert_not_called()

    @pytest.mark.parametrize("is_valid, expected_insert", [
        (True, True),
        (False, False)
    ])
    def test_process_row(self, mock_selenium, mock_mysql, is_valid, expected_insert):
        # Mock selenium returns for processRow
        mock_selenium.getText.side_effect = ["Job Title", "Company Name", "Location"] if is_valid else ["", "", ""]
        mock_selenium.getElms.return_value = [MagicMock(text="Company Name")]
        mock_selenium.getUrl.return_value = "http://job.url?jl=123"
        mock_selenium.getHtml.return_value = "<p>Description</p>"
        
        with patch('scrapper.glassdoor.validate', return_value=is_valid), \
             patch('scrapper.glassdoor.htmlToMarkdown', return_value="Description"), \
             patch('scrapper.glassdoor.mergeDuplicatedJobs') as mock_merge:
            
            mock_mysql.insert.return_value = 1
            
            if is_valid:
                processRow()
                mock_mysql.insert.assert_called_once()
                mock_merge.assert_called_once()
            else:
                try:
                    processRow()
                except ValueError:
                    pass
                mock_mysql.insert.assert_not_called()

    def test_login_flow(self, mock_selenium, mock_env_vars):
        with patch('scrapper.glassdoor.loadMainPage') as mock_load_main, \
             patch('scrapper.glassdoor.sleep'), \
             patch('scrapper.glassdoor.USER_EMAIL', 'test@email.com'), \
             patch('scrapper.glassdoor.USER_PWD', 'password'):
            
            login()
            
            mock_load_main.assert_called_once()
            mock_selenium.sendKeys.assert_any_call('#inlineUserEmail', 'test@email.com')
            mock_selenium.waitAndClick.assert_called()
