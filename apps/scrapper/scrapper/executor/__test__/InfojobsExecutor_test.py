import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.InfojobsExecutor import InfojobsExecutor
from scrapper.navigator.infojobsNavigator import InfojobsNavigator
from scrapper.services.InfojobsService import InfojobsService
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
    with patch('scrapper.executor.InfojobsExecutor.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestInfojobsExecutor:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        with patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            executor = InfojobsExecutor(mock_selenium, mock_persistence_manager)
            executor.run(preload_page=True)
            mock_nav.load_search_page.assert_called_once()
            if not mock_selenium.driverUtil.useUndetected:
                mock_nav.security_filter.assert_called_once()
    
    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator'), \
             patch('scrapper.executor.InfojobsExecutor.InfojobsService') as mock_service_cls, \
             patch('scrapper.executor.BaseExecutor.MysqlUtil'), \
             patch.object(InfojobsExecutor, '_process_keyword') as mock_process_keyword:
            
            mock_service = mock_service_cls.return_value
            mock_service.should_skip_keyword.return_value = (False, 1)

            executor = InfojobsExecutor(mock_selenium, mock_persistence_manager)
            executor.run(preload_page=False)
            assert mock_process_keyword.called
            mock_persistence_manager.finalize_scrapper.assert_called_with('INFOJOBS')

    def test_process_keyword_flow(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch.object(InfojobsExecutor, '_load_and_process_row', return_value=False) as mock_row, \
             patch('scrapper.executor.InfojobsExecutor.InfojobsNavigator') as mock_nav_class:
            
            executor = InfojobsExecutor(mock_selenium, mock_persistence_manager)
            executor.service = MagicMock()
            mock_nav = executor.navigator
            mock_nav.load_filtered_search_results.return_value = True
            mock_nav.get_total_results.return_value = 10
            mock_nav.fast_forward_page.return_value = 1
            mock_nav.click_next_page.return_value = False
            
            executor._process_keyword("python", start_page=1)
            
            mock_nav.load_search_page.assert_called()
            mock_nav.load_filtered_search_results.assert_called_with('python')
            assert mock_row.call_count == 10

class TestInfojobsService:
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return InfojobsService(mock_mysql, mock_persistence_manager)

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
        with patch('scrapper.services.InfojobsService.htmlToMarkdown', return_value="Markdown"), \
             patch('scrapper.services.InfojobsService.validate', return_value=True), \
             patch('scrapper.services.InfojobsService.mergeDuplicatedJobs'):
             
             mock_mysql.insert.return_value = 1
             result = service.process_job("Title", "Company", "Location", "https://www.infojobs.net/of-123", "<html>")
             
             assert result is True
             mock_mysql.insert.assert_called_once()
