import pytest
from unittest.mock import MagicMock
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.GlassdoorService import GlassdoorService

class TestGlassdoorService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def service(self, mock_mysql):
        mock_persistence_manager = MagicMock(spec=PersistenceManager)
        return GlassdoorService(mock_mysql, mock_persistence_manager)
    
    def test_initialization(self, service):
        assert service.web_page == 'Glassdoor'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.glassdoor.es/job-listing/?jl=1009552660667", "1009552660667"),
        ("https://www.glassdoor.es/job-listing/?jobListingId=1009552660667", "1009552660667"),
        ("https://www.glassdoor.es/job-listing/test?JL=12345&other=param", "12345"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
