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
    def service(self, mock_mysql):
        mock_persistence_manager = MagicMock(spec=PersistenceManager)
        return TecnoempleoService(mock_mysql, mock_persistence_manager)
    
    def test_initialization(self, service):
        assert service.web_page == 'Tecnoempleo'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.tecnoempleo.com/integration-specialist/rf-b14e1d3282dea3a42b40", "rf-b14e1d3282dea3a42b40"),
        ("https://www.tecnoempleo.com/job/rf-xyz123", "rf-xyz123"),
        ("https://www.tecnoempleo.com/test/abc", "abc"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
