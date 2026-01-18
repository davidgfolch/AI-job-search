import pytest
from unittest.mock import MagicMock
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.TecnoempleoService import TecnoempleoService

class TestTecnoempleoService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return TecnoempleoService(mock_mysql, mock_persistence_manager)
    
    def test_initialization(self, service):
        assert service.web_page == 'Tecnoempleo'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("http://tecnoempleo.com/job-title/rf-1234567890", "rf-1234567890"),
        ("http://tecnoempleo.com/another/rf-0987654321?param=value", "rf-0987654321?param=value"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
