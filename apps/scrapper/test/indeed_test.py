import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import indeed
from scrapper.indeed import run, searchJobs, loadAndProcessRow, processRow, getJobId, postProcessMarkdown
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    with patch('scrapper.indeed.selenium', spec=SeleniumService) as mock:
        yield mock

@pytest.fixture
def mock_mysql():
    with patch('scrapper.indeed.mysql', spec=MysqlUtil) as mock:
        yield mock

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.indeed.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestIndeedScrapper:

    def test_run_preload_page(self, mock_selenium, mock_env_vars):
        mock_selenium_instance = MagicMock(spec=SeleniumService)
        
        with patch('scrapper.indeed.JOBS_SEARCH', 'python developer'), \
             patch('scrapper.indeed.searchJobs') as mock_search_jobs:
            run(mock_selenium_instance, preloadPage=True)
            mock_search_jobs.assert_called_with('python developer', True)
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        mock_selenium_instance = MagicMock(spec=SeleniumService)
        
        # Patch MysqlUtil class because run() instantiates it
        with patch('scrapper.indeed.MysqlUtil') as mock_mysql_class:
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance
            
            mock_persistence_manager.get_state.return_value = {}
            
            # Mock searchJobs to avoid actual execution loop
            with patch('scrapper.indeed.searchJobs') as mock_search_jobs:
                run(mock_selenium_instance, preloadPage=False, persistenceManager=mock_persistence_manager)
                
                assert mock_search_jobs.called
                mock_persistence_manager.get_state.assert_called_with('Indeed')
                mock_persistence_manager.clear_state.assert_called_with('Indeed')

    def test_get_job_id(self):
        url = "https://es.indeed.com/viewjob?jk=1234567890&other=param"
        assert getJobId(url) == "1234567890"
        
        url2 = "https://es.indeed.com/pagead/clk?mo=r&ad=...&jk=0987654321&..."
        assert getJobId(url2) == "0987654321"

    def test_search_jobs_pagination(self, mock_selenium, mock_mysql):
        # Setup mocks for searchJobs
        
        with patch('scrapper.indeed.getUrl', return_value="http://test.url"), \
             patch('scrapper.indeed.acceptCookies'), \
             patch('scrapper.indeed.clickNextPage', side_effect=[True, False]), \
             patch('scrapper.indeed.loadAndProcessRow', return_value=True) as mock_process_row, \
             patch('scrapper.indeed.summarize'):
            
            searchJobs("python", securityFilter=False, startPage=1)
            
            # Should process jobs (15 per page * 2 pages roughly, but loop condition depends on clickNextPage)
            # clickNextPage returns True once, then False.
            # Loop runs:
            # 1. page 1. process 15 jobs. clickNextPage -> True.
            # 2. page 2. process 15 jobs. clickNextPage -> False. Break.
            assert mock_process_row.call_count == 30 

    def test_process_row_insert(self, mock_selenium, mock_mysql):
        # Mock selenium returns for processRow
        mock_selenium.getText.side_effect = ["Job Title\n- job post", "Company Name", "Location"]
        mock_selenium.getElms.return_value = [] # For easyApply check
        mock_selenium.getHtml.return_value = "<p>Description</p>"
        
        # Mock validation and mysql
        with patch('scrapper.indeed.validate', return_value=True), \
             patch('scrapper.indeed.htmlToMarkdown', return_value="Description"), \
             patch('scrapper.indeed.mergeDuplicatedJobs'), \
             patch('scrapper.indeed.getJobId', return_value="123"):
            
            mock_mysql.insert.return_value = 1
            
            result = processRow("http://job.url")
            
            assert result is True
            mock_mysql.insert.assert_called_once()
            assert "Job Title" in mock_mysql.insert.call_args[0][0]
            assert "Company Name" in mock_mysql.insert.call_args[0][0]

    def test_process_row_validation_fail(self, mock_selenium, mock_mysql):
        mock_selenium.getText.return_value = "" # Empty title
        
        with patch('scrapper.indeed.validate', return_value=False), \
             patch('scrapper.indeed.getJobId', return_value="123"), \
             patch('scrapper.indeed.htmlToMarkdown', return_value="Desc"):
            
            result = processRow("http://job.url")
            
            assert result is False
            mock_mysql.insert.assert_not_called()

    def test_post_process_markdown(self):
        md = "Check [this link](/ofertas-trabajo/123) for details."
        processed = postProcessMarkdown(md)
        assert "this link" in processed
        assert "/ofertas-trabajo/123" not in processed
