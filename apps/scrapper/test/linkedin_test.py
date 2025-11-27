import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import linkedin
from scrapper.linkedin import run, searchJobs, loadAndProcessRow, processRow, getJobId, getJobUrlShort
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    with patch('scrapper.linkedin.selenium', spec=SeleniumUtil) as mock:
        yield mock

@pytest.fixture
def mock_mysql():
    with patch('scrapper.linkedin.mysql', spec=MysqlUtil) as mock:
        yield mock

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.linkedin.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestLinkedinScrapper:

    def test_run_preload_page(self, mock_selenium, mock_env_vars):
        mock_selenium_instance = MagicMock(spec=SeleniumUtil)
        
        with patch('scrapper.linkedin.login') as mock_login:
            run(mock_selenium_instance, preloadPage=True)
            mock_login.assert_called_once()
            mock_selenium_instance.waitUntilPageUrlContains.assert_called()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        mock_selenium_instance = MagicMock(spec=SeleniumUtil)
        
        # Patch MysqlUtil class because run() instantiates it
        with patch('scrapper.linkedin.MysqlUtil') as mock_mysql_class:
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance
            
            mock_persistence_manager.get_state.return_value = {}
            
            # Mock searchJobs to avoid actual execution loop
            with patch('scrapper.linkedin.loadPage'), \
                 patch('scrapper.linkedin.checkLoginPopup'), \
                 patch('scrapper.linkedin.checkResults', return_value=True), \
                 patch('scrapper.linkedin.searchJobs') as mock_search_jobs:
                
                run(mock_selenium_instance, preloadPage=False, persistenceManager=mock_persistence_manager)
                
                assert mock_search_jobs.called
                mock_persistence_manager.get_state.assert_called_with('Linkedin')
                mock_persistence_manager.clear_state.assert_called_with('Linkedin')

    def test_get_job_id(self):
        url = "https://www.linkedin.com/jobs/view/1234567890/?other=param"
        assert getJobId(url) == 1234567890
        
        url2 = "https://www.linkedin.com/jobs/view/0987654321/"
        assert getJobId(url2) == 987654321

    def test_get_job_url_short(self):
        url = "https://www.linkedin.com/jobs/view/1234567890/?other=param"
        assert getJobUrlShort(url) == "https://www.linkedin.com/jobs/view/1234567890/"

    def test_search_jobs_pagination(self, mock_selenium, mock_mysql):
        # Setup mocks for searchJobs
        
        with patch('scrapper.linkedin.getTotalResultsFromHeader', return_value=30), \
             patch('scrapper.linkedin.clickNextPage', side_effect=[True, False]), \
             patch('scrapper.linkedin.loadAndProcessRow', return_value=True) as mock_process_row, \
             patch('scrapper.linkedin.summarize'):
            
            searchJobs("python", startPage=1)
            
            # Should process jobs (25 per page * 2 pages roughly, but loop condition depends on clickNextPage)
            # clickNextPage returns True once, then False.
            # Loop runs:
            # 1. page 1. process 25 jobs. clickNextPage -> True.
            # 2. page 2. process 5 jobs (total 30). clickNextPage -> False. Break.
            assert mock_process_row.call_count == 30

    def test_process_row_insert(self, mock_selenium, mock_mysql):
        # Mock selenium returns for processRow
        # Mock getJobDataInList
        mock_selenium.getText.side_effect = ["Job Title", "Company Name", "Location"]
        mock_selenium.getAttr.return_value = "https://www.linkedin.com/jobs/view/123/"
        mock_selenium.getHtml.return_value = "<p>Description</p>"
        
        # Mock validation and mysql
        with patch('scrapper.linkedin.validate', return_value=True), \
             patch('scrapper.linkedin.htmlToMarkdown', return_value="Description"), \
             patch('scrapper.linkedin.mergeDuplicatedJobs'), \
             patch('scrapper.linkedin.getJobId', return_value=123):
            
            mock_mysql.insert.return_value = 1
            
            # processRow(idx) calls getJobDataInList(idx)
            processRow(1)
            
            mock_mysql.insert.assert_called_once()
            assert "Job Title" in mock_mysql.insert.call_args[0][0]
            assert "Company Name" in mock_mysql.insert.call_args[0][0]

    def test_process_row_validation_fail(self, mock_selenium, mock_mysql):
        # Mock getJobDataInList
        mock_selenium.getText.return_value = "" # Empty title
        mock_selenium.getAttr.return_value = "https://www.linkedin.com/jobs/view/123/"
        
        with patch('scrapper.linkedin.validate', return_value=False), \
             patch('scrapper.linkedin.getJobId', return_value=123), \
             patch('scrapper.linkedin.htmlToMarkdown', return_value="Desc"):
            
            with pytest.raises(ValueError, match='Validation failed'):
                processRow(1)
            
            mock_mysql.insert.assert_not_called()
