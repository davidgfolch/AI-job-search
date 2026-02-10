import pytest
from unittest.mock import MagicMock, patch
from scrapper.executor.TecnoempleoExecutor import TecnoempleoExecutor
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
    with patch('scrapper.executor.TecnoempleoExecutor.getAndCheckEnvVars') as mock:
        mock.return_value = ('test@email.com', 'password', 'python developer')
        yield mock

class TestTecnoempleoExecutor:

    def test_run_preload_page(self, mock_selenium, mock_env_vars, mock_persistence_manager):
        with patch('scrapper.executor.TecnoempleoExecutor.TecnoempleoNavigator') as mock_nav_class:
            mock_nav = mock_nav_class.return_value
            # Explicitly mock selenium attribute which is accessed in _preload_action
            mock_nav.selenium = MagicMock()

            executor = TecnoempleoExecutor(mock_selenium, mock_persistence_manager, False)
            executor.run(preload_page=True)
            
            mock_nav.load_page.assert_called_once()
            mock_nav.login.assert_called_once()
            mock_nav.selenium.waitUntilPageUrlContains.assert_called()

    def test_run_normal_execution(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.TecnoempleoExecutor.TecnoempleoNavigator'), \
             patch('scrapper.executor.TecnoempleoExecutor.TecnoempleoService') as mock_service_cls, \
             patch('scrapper.executor.BaseExecutor.MysqlUtil'), \
             patch.object(TecnoempleoExecutor, '_process_keyword') as mock_process_keyword:
             
             mock_service = mock_service_cls.return_value
             mock_service.should_skip_keyword.return_value = (False, 1)

             executor = TecnoempleoExecutor(mock_selenium, mock_persistence_manager, False)
             executor.run(preload_page=False)
             mock_process_keyword.assert_called()

    def test_process_keyword_flow(self, mock_selenium, mock_persistence_manager, mock_env_vars):
         with patch.object(TecnoempleoExecutor, '_load_and_process_row', return_value=(True, False)) as mock_row, \
              patch('scrapper.executor.TecnoempleoExecutor.TecnoempleoNavigator'):
             
             executor = TecnoempleoExecutor(mock_selenium, mock_persistence_manager, False)
             executor.service = MagicMock()
             mock_nav = executor.navigator
             mock_nav.check_results.return_value = True
             mock_nav.get_total_results.return_value = 30
             mock_nav.fast_forward_page.return_value = 1
             mock_nav.click_next_page.side_effect = [False]
             
             executor._process_keyword('python', 1)
             
             mock_nav.load_page.assert_called()
             mock_nav.accept_cookies.assert_called()
             # 30 items -> 30 calls
             assert mock_row.call_count == 30

    def test_load_and_process_row(self, mock_selenium, mock_persistence_manager, mock_env_vars):
        with patch('scrapper.executor.TecnoempleoExecutor.TecnoempleoNavigator'):
            executor = TecnoempleoExecutor(mock_selenium, mock_persistence_manager, False)
            mock_nav = executor.navigator
            mock_svc = MagicMock(spec=TecnoempleoService)
            executor.service = mock_svc
            
            mock_nav.scroll_jobs_list.return_value = "cssSel"
            mock_nav.get_attribute.return_value = "http://job.url"
            mock_svc.job_exists_in_db.return_value = ("123", False)
            mock_nav.load_detail.return_value = True
            mock_nav.get_job_data.return_value = ("Title", "Company", "Location", "URL", "HTML")
            mock_svc.process_job.return_value = True
            
            ok, exists = executor._load_and_process_row(0, 0)
            assert ok is True
            assert exists is False
            mock_svc.process_job.assert_called()
            mock_nav.go_back.assert_called()

class TestTecnoempleoService:
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return TecnoempleoService(mock_mysql, mock_persistence_manager, False)
        
    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="Markdown"), \
             patch('scrapper.services.TecnoempleoService.validate', return_value=True), \
             patch('scrapper.services.TecnoempleoService.find_last_duplicated'):
             
             mock_mysql.insert.return_value = 1
             result = service.process_job("Title", "Company", "Location", "http://url/rf-123", "<html>")
             
             assert result is True
             mock_mysql.insert.assert_called_once()
