import pytest
from unittest.mock import MagicMock, patch
from scrapper import infojobs
from scrapper.infojobs import run
from scrapper.selenium.infojobs_selenium import InfojobsNavigator
from scrapper.services.job_services.infojobs_job_service import InfojobsJobService
from scrapper.services.selenium.seleniumService import SeleniumService
from scrapper.persistence_manager import PersistenceManager
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
def mock_navigator():
    return MagicMock(spec=InfojobsNavigator)

@pytest.fixture
def mock_service():
    return MagicMock(spec=InfojobsJobService)

@pytest.fixture
def mock_env_vars():
    with patch('scrapper.infojobs.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestInfojobsScrapper:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager, mock_navigator):
        with patch('scrapper.infojobs.InfojobsNavigator', return_value=mock_navigator):
            run(mock_selenium, preloadPage=True, persistenceManager=mock_persistence_manager)
            
            mock_navigator.load_search_page.assert_called_once()
            # Depending on useUndetected, security_filter might be called
            if not mock_selenium.usesUndetectedDriver():
                mock_navigator.security_filter.assert_called_once()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars, mock_navigator, mock_service):
        with patch('scrapper.infojobs.InfojobsNavigator', return_value=mock_navigator), \
             patch('scrapper.infojobs.InfojobsJobService', return_value=mock_service), \
             patch('scrapper.infojobs.MysqlUtil'), \
             patch('scrapper.infojobs.JOBS_SEARCH', 'python developer'):
            
            mock_service.should_skip_keyword.return_value = (False, 1)
            mock_navigator.load_filtered_search_results.return_value = True
            mock_navigator.get_total_results_from_header.return_value = 10
            mock_navigator.click_next_page.return_value = False
            
            mock_job_link = MagicMock()
            mock_navigator.get_job_link_element.return_value = mock_job_link
            mock_navigator.get_job_url.return_value = "http://job.url"
            
            mock_service.job_exists_in_db.return_value = (123, False)
            mock_navigator.get_job_data.return_value = ("Title", "Company", "Location", "HTML")
            mock_service.process_job.return_value = True

            run(mock_selenium, preloadPage=False, persistenceManager=mock_persistence_manager)
            
            mock_service.prepare_resume.assert_called_once()
            mock_service.clear_state.assert_called_once()
            mock_navigator.load_search_page.assert_called()
            mock_navigator.load_filtered_search_results.assert_called_with('python developer')

class TestInfojobsJobService:
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return InfojobsJobService(mock_mysql, mock_persistence_manager)

    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.infojobs.net/of-1234567890?other=param", "1234567890"),
        ("https://www.infojobs.net/of-0987654321", "0987654321"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id

    def test_job_exists_in_db(self, service, mock_mysql):
        mock_mysql.fetchOne.return_value = {"id": 1}
        job_id, exists = service.job_exists_in_db("https://www.infojobs.net/of-123")
        assert job_id == "123"
        assert exists is True

    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.services.job_services.infojobs_job_service.htmlToMarkdown', return_value="Markdown"), \
             patch('scrapper.services.job_services.infojobs_job_service.validate', return_value=True), \
             patch('scrapper.services.job_services.infojobs_job_service.mergeDuplicatedJobs'):
             
             mock_mysql.insert.return_value = 1
             result = service.process_job("Title", "Company", "Location", "https://www.infojobs.net/of-123", "<html>")
             
             assert result is True
             mock_mysql.insert.assert_called_once()
