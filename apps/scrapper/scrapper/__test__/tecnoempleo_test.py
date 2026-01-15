import pytest
from unittest.mock import MagicMock, patch
from scrapper import tecnoempleo
from scrapper.tecnoempleo import run
from scrapper.navigator.tecnoempleoNavigator import TecnoempleoNavigator
from scrapper.services.TecnoempleoService import TecnoempleoService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.util.persistence_manager import PersistenceManager
from commonlib.mysqlUtil import MysqlUtil

@pytest.fixture
def mock_selenium():
    mock = MagicMock(spec=SeleniumService)
    mock.driverUtil = MagicMock()
    mock.driverUtil.useUndetected = False
    return mock

@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.tecnoempleo.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestTecnoempleoScrapper:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        mock_navigator = MagicMock(spec=TecnoempleoNavigator)
        
        with patch('scrapper.tecnoempleo.TecnoempleoNavigator', return_value=mock_navigator):
            run(mock_selenium, preloadPage=True, persistenceManager=mock_persistence_manager)
            
            mock_navigator.load_page.assert_called_once()
            mock_navigator.login.assert_called_once()
            mock_navigator.wait_until_page_url_contains.assert_called()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        mock_navigator = MagicMock(spec=TecnoempleoNavigator)
        mock_service = MagicMock(spec=TecnoempleoService)
        
        with patch('scrapper.tecnoempleo.TecnoempleoNavigator', return_value=mock_navigator), \
             patch('scrapper.tecnoempleo.TecnoempleoService', return_value=mock_service), \
             patch('scrapper.tecnoempleo.MysqlUtil'), \
             patch('scrapper.tecnoempleo.JOBS_SEARCH', 'python developer'):
             
             mock_service.should_skip_keyword.return_value = (False, 1)
             mock_navigator.check_results.return_value = True
             mock_navigator.get_total_results_from_header.return_value = 30
             mock_navigator.click_next_page.side_effect = [False] # Stop at page 1
             mock_navigator.scroll_jobs_list.return_value = "cssSel"
             mock_navigator.get_attribute.return_value = "http://job.url"
             mock_service.job_exists_in_db.return_value = ("123", False)
             mock_navigator.load_detail.return_value = True
             mock_navigator.get_job_data.return_value = ("Title", "Company", "Location", "URL", "HTML")
             mock_service.process_job.return_value = True

             run(mock_selenium, preloadPage=False, persistenceManager=mock_persistence_manager)
             
             mock_service.prepare_resume.assert_called_once()
             mock_navigator.load_page.assert_called()
             mock_navigator.get_total_results_from_header.assert_called()
             mock_service.process_job.assert_called()


class TestTecnoempleoService:
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return TecnoempleoService(mock_mysql, mock_persistence_manager)
        
    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="Markdown"), \
             patch('scrapper.services.TecnoempleoService.validate', return_value=True), \
             patch('scrapper.services.TecnoempleoService.mergeDuplicatedJobs'):
             
             mock_mysql.insert.return_value = 1
             result = service.process_job("Title", "Company", "Location", "http://url/rf-123", "<html>")
             
             assert result is True
             mock_mysql.insert.assert_called_once()
             
class TestTecnoempleoNavigator:
     # Add basic tests or assume verified by run
     pass
