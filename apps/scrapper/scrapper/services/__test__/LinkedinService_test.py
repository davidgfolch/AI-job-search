import pytest
from unittest.mock import MagicMock
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.LinkedinService import LinkedinService

class TestLinkedinService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def service(self, mock_mysql):
        mock_persistence_manager = MagicMock(spec=PersistenceManager)
        return LinkedinService(mock_mysql, mock_persistence_manager)
    
    def test_initialization(self, service):
        assert service.web_page == 'Linkedin'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.linkedin.com/jobs/view/12345/", 12345),
        ("https://www.linkedin.com/jobs/view/67890/other-params", 67890),
        ("https://www.linkedin.com/jobs/view/111/", 111),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
    
    @pytest.mark.parametrize("url, expected_short", [
        ("https://www.linkedin.com/jobs/view/12345/other-params", "https://www.linkedin.com/jobs/view/12345/"),
        ("https://www.linkedin.com/jobs/view/67890/", "https://www.linkedin.com/jobs/view/67890/"),
    ])
    def test_get_job_url_short(self, service, url, expected_short):
        assert service.get_job_url_short(url) == expected_short
    
    def test_job_exists_in_db(self, service, mock_mysql):
        mock_mysql.fetchOne.return_value = {"id": 1}
        url = "https://www.linkedin.com/jobs/view/12345/"
        job_id, exists = service.job_exists_in_db(url)
        assert job_id == 12345
        assert exists is True
