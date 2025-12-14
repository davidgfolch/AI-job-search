import pytest
from unittest.mock import MagicMock, patch, call
from scrapper import infojobs
from scrapper.infojobs import run, searchJobs, loadAndProcessRow, processRow, getJobId, postProcessMarkdown
from scrapper.seleniumUtil import SeleniumUtil
from scrapper.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil
from itertools import cycle

@pytest.fixture
def mock_selenium():
    with patch('scrapper.infojobs.selenium', spec=SeleniumUtil) as mock:
        yield mock

@pytest.fixture
def mock_mysql():
    with patch('scrapper.infojobs.mysql', spec=MysqlUtil) as mock:
        yield mock

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.infojobs.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestInfojobsScrapper:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        mock_selenium_instance = MagicMock(spec=SeleniumUtil)
        
        with patch('scrapper.infojobs.JOBS_SEARCH', 'python developer'), \
             patch('scrapper.infojobs.searchJobs') as mock_search_jobs:
            run(mock_selenium_instance, preloadPage=True, persistenceManager=mock_persistence_manager)
            # JOBS_SEARCH is 'python developer', split by comma gives ['python developer']
            # run calls searchJobs(JOBS_SEARCH.split(',')[0], True, 1, persistenceManager)
            mock_search_jobs.assert_called_with('python developer', True, 1, mock_persistence_manager)
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        mock_selenium_instance = MagicMock(spec=SeleniumUtil)
        
        # Patch MysqlUtil class because run() instantiates it
        with patch('scrapper.infojobs.MysqlUtil') as mock_mysql_class:
            mock_mysql_instance = MagicMock(spec=MysqlUtil)
            mock_mysql_class.return_value.__enter__.return_value = mock_mysql_instance
            
            mock_persistence_manager.get_state.return_value = {}
            mock_persistence_manager.should_skip_keyword.return_value = (False, 1)
            
            # Mock searchJobs to avoid actual execution loop
            with patch('scrapper.infojobs.searchJobs') as mock_search_jobs:
                run(mock_selenium_instance, preloadPage=False, persistenceManager=mock_persistence_manager)
                
                assert mock_search_jobs.called
                mock_persistence_manager.prepare_resume.assert_called_with('Infojobs')
                mock_persistence_manager.clear_state.assert_called_with('Infojobs')

    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.infojobs.net/of-1234567890?other=param", "1234567890"),
        ("https://www.infojobs.net/of-0987654321", "0987654321"),
    ])
    def test_get_job_id(self, url, expected_id):
        assert getJobId(url) == expected_id

    def test_search_jobs_pagination(self, mock_selenium, mock_mysql, mock_persistence_manager):
        # Setup mocks for searchJobs
        
        with patch('scrapper.infojobs.loadSearchPage'), \
             patch('scrapper.infojobs.loadFilteredSearchResults', return_value=True), \
             patch('scrapper.infojobs.getTotalResultsFromHeader', return_value=30), \
             patch('scrapper.infojobs.clickNextPage', side_effect=[True, False]), \
             patch('scrapper.infojobs.loadAndProcessRow', return_value=True) as mock_process_row, \
             patch('scrapper.infojobs.summarize'):
            
            searchJobs("python", preloadPage=False, startPage=1, persistenceManager=mock_persistence_manager)
            
            # Should process jobs (22 per page * 2 pages roughly, but loop condition depends on clickNextPage)
            # clickNextPage returns True once, then False.
            # Loop runs:
            # 1. page 1. process 22 jobs. clickNextPage -> True.
            # 2. page 2. process 8 jobs (total 30). clickNextPage -> False. Break.
            assert mock_process_row.call_count == 30

    @pytest.mark.parametrize("scenario", [
        {"desc": "valid_insert", "title": "Job Title", "valid": True},
        {"desc": "validation_fail", "title": "", "valid": False}
    ])
    def test_process_row(self, mock_selenium, mock_mysql, scenario):
        # Mock selenium returns for processRow
        mock_selenium.getText.side_effect = cycle([scenario["title"], "Company Name", "Location"]) if scenario["valid"] else cycle(["", "", ""])
        mock_selenium.getHtml.return_value = "<p>Description</p>"
        
        with patch('scrapper.infojobs.validate', return_value=scenario["valid"]), \
             patch('scrapper.infojobs.htmlToMarkdown', return_value="Description"), \
             patch('scrapper.infojobs.mergeDuplicatedJobs'), \
             patch('scrapper.infojobs.getJobId', return_value="123"):
            
            mock_mysql.insert.return_value = 1
            
            result = processRow("http://job.url")
            
            assert result is scenario["valid"]
            if scenario["valid"]:
                mock_mysql.insert.assert_called_once()
                assert "Job Title" in mock_mysql.insert.call_args[0][0]
            else:
                mock_mysql.insert.assert_not_called()

    def test_post_process_markdown(self):
        md = "Check [this link](/ofertas-trabajo/123) for details."
        # infojobs.postProcessMarkdown calls removeLinks
        with patch('scrapper.infojobs.removeLinks', return_value="Check this link for details."):
            processed = postProcessMarkdown(md)
            assert "this link" in processed
            assert "/ofertas-trabajo/123" not in processed
