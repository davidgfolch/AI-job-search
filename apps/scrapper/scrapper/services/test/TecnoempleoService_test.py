import pytest
from unittest.mock import MagicMock, patch
from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from commonlib.sql.mysqlUtil import MysqlUtil
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
        return TecnoempleoService(mock_mysql, mock_persistence_manager, False)
    
    def test_initialization(self, service):
        assert service.web_page == 'Tecnoempleo'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("http://tecnoempleo.com/job-title/rf-1234567890", "rf-1234567890"),
        ("http://tecnoempleo.com/another/rf-0987654321?param=value", "rf-0987654321?param=value"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id

    def test_process_job_unspecified_company(self, service, mock_mysql):
        """A job without company is inserted, and not linked as duplicated, while the company is unspecified"""
        mock_mysql.insert.return_value = 1
        with patch('scrapper.services.TecnoempleoService.htmlToMarkdown', return_value="Markdown"):
            result = service.process_job("Title", UNSPECIFIED_COMPANY, "Location", "http://url/rf-123", "<html>")
        assert result is True
        params = mock_mysql.insert.call_args[0][0]
        assert params[2] == UNSPECIFIED_COMPANY
        assert params[-1] is None
        mock_mysql.fetchAll.assert_not_called()
