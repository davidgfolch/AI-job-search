import pytest
from unittest.mock import MagicMock
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.BaseService import BaseService

class ConcreteService(BaseService):
    def get_job_id(self, url: str) -> str:
        return url.split('/')[-1]

class TestBaseService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return ConcreteService(mock_mysql, mock_persistence_manager, 'TestPage', False)
    
    def test_initialization(self, service, mock_mysql, mock_persistence_manager):
        assert service.mysql == mock_mysql
        assert service.persistence_manager == mock_persistence_manager
        assert service.web_page == 'TestPage'
        assert service.debug is False
    

    
    @pytest.mark.parametrize("url, job_exists, expected_job_id", [
        ("http://example.com/jobs/12345", True, "12345"),
        ("http://example.com/jobs/67890", False, "67890"),
    ])
    def test_job_exists_in_db(self, service, mock_mysql, url, job_exists, expected_job_id):
        mock_mysql.fetchOne.return_value = {"id": 1} if job_exists else None
        job_id, exists = service.job_exists_in_db(url)
        assert job_id == expected_job_id
        assert exists == job_exists
    
    def test_prepare_resume(self, service, mock_persistence_manager):
        service.prepare_resume()
        mock_persistence_manager.prepare_resume.assert_called_once_with('TestPage')
    
    def test_should_skip_keyword(self, service, mock_persistence_manager):
        mock_persistence_manager.should_skip_keyword.return_value = True
        assert service.should_skip_keyword('python') is True
        mock_persistence_manager.should_skip_keyword.assert_called_once_with('python')
    
    def test_update_state(self, service, mock_persistence_manager):
        service.update_state('python', 5)
        mock_persistence_manager.update_state.assert_called_once_with('TestPage', 'python', 5)
    
    def test_clear_state(self, service, mock_persistence_manager):
        service.clear_state()
        mock_persistence_manager.clear_state.assert_called_once_with('TestPage')
    
    def test_post_process_markdown_default(self, service):
        md = "# Test\nContent"
        assert service.post_process_markdown(md) == md
