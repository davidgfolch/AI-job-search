import pytest
from unittest.mock import MagicMock, patch
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.GlassdoorService import GlassdoorService

class TestGlassdoorService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return GlassdoorService(mock_mysql, mock_persistence_manager)
    
    def test_initialization(self, service):
        assert service.web_page == 'Glassdoor'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.glassdoor.es/job-listing/?jl=1009552660667", "1009552660667"),
        ("https://www.glassdoor.es/job-listing/?jobListingId=1009552660667", "1009552660667"),
        ("https://www.glassdoor.es/job-listing/test?JL=12345&other=param", "12345"),
        ("https://www.glassdoor.es/job-listing/test?jl=1234567890&other=param", "1234567890"),
        ("https://www.glassdoor.es/job-listing/test?jobListingId=0987654321&other=param", "0987654321"),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
    
    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.services.GlassdoorService.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.GlassdoorService.validate', return_value=True), \
             patch('scrapper.services.GlassdoorService.mergeDuplicatedJobs'):
            mock_mysql.insert.return_value = 1
            result = service.process_job("Title", "Company", "Loc", "http://url?jl=123", "HTML", False)
            assert result is True
            mock_mysql.insert.assert_called_once()
    
    def test_process_job_invalid(self, service):
        with patch('scrapper.services.GlassdoorService.validate', return_value=False):
            with pytest.raises(ValueError):
                service.process_job("T", "C", "L", "U", "H", False)
