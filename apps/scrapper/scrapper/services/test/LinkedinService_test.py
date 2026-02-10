import pytest
from unittest.mock import MagicMock, patch
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.services.LinkedinService import LinkedinService

class TestLinkedinService:
    @pytest.fixture
    def mock_mysql(self):
        return MagicMock(spec=MysqlUtil)
    
    @pytest.fixture
    def mock_persistence_manager(self):
        return MagicMock(spec=PersistenceManager)
    
    @pytest.fixture
    def service(self, mock_mysql, mock_persistence_manager):
        return LinkedinService(mock_mysql, mock_persistence_manager, False)
    
    def test_initialization(self, service):
        assert service.web_page == 'Linkedin'
    
    @pytest.mark.parametrize("url, expected_id", [
        ("https://www.linkedin.com/jobs/view/12345/", 12345),
        ("https://www.linkedin.com/jobs/view/67890/other-params", 67890),
        ("https://www.linkedin.com/jobs/view/111/", 111),
        ("https://www.linkedin.com/jobs/view/123456/?x=y", 123456),
    ])
    def test_get_job_id(self, service, url, expected_id):
        assert service.get_job_id(url) == expected_id
    
    @pytest.mark.parametrize("url, expected_short", [
        ("https://www.linkedin.com/jobs/view/12345/other-params", "https://www.linkedin.com/jobs/view/12345/"),
        ("https://www.linkedin.com/jobs/view/67890/", "https://www.linkedin.com/jobs/view/67890/"),
        ("https://www.linkedin.com/jobs/view/123456/?x=y", "https://www.linkedin.com/jobs/view/123456/"),
    ])
    def test_get_job_url_short(self, service, url, expected_short):
        assert service.get_job_url_short(url) == expected_short
    
    @pytest.mark.parametrize("fetch_result, expected_exists", [
        ({"id": 1}, True),
        (None, False),
    ])
    def test_job_exists_in_db(self, service, mock_mysql, fetch_result, expected_exists):
        mock_mysql.fetchOne.return_value = fetch_result
        url = "https://www.linkedin.com/jobs/view/12345/"
        job_id, exists = service.job_exists_in_db(url)
        assert job_id == 12345
        assert exists is expected_exists
    
    def test_process_job_valid(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.LinkedinService.find_last_duplicated'):
            mock_mysql.jobExists.return_value = False
            mock_mysql.insert.return_value = 1
            service.process_job("Title", "Company", "Loc", "https://www.linkedin.com/jobs/view/123/", "HTML", False, False)
            mock_mysql.insert.assert_called()
    
    def test_process_job_invalid(self, service):
        with patch('scrapper.core.baseScrapper.validate', return_value=False):
            with pytest.raises(ValueError):
                service.process_job("T", "C", "L", "U", "H", False, False)
    
    def test_process_job_existing_direct_url(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"):
            mock_mysql.jobExists.return_value = True
            service.process_job("Title", "Company", "Loc", "https://www.linkedin.com/jobs/view/123/", "HTML", True, False)
            mock_mysql.insert.assert_not_called()
    
    def test_prepare_resume(self, service, mock_persistence_manager):
        service.prepare_resume()
        mock_persistence_manager.prepare_resume.assert_called_with('Linkedin')
    
    def test_should_skip_keyword(self, service, mock_persistence_manager):
        mock_persistence_manager.should_skip_keyword.return_value = (True, 1)
        assert service.should_skip_keyword('python') == (True, 1)
        mock_persistence_manager.should_skip_keyword.assert_called_with('python')
    
    def test_update_state(self, service, mock_persistence_manager):
        service.update_state('python', 5)
        mock_persistence_manager.update_state.assert_called_with('Linkedin', 'python', 5)
    
    def test_clear_state(self, service, mock_persistence_manager):
        service.clear_state()
        mock_persistence_manager.clear_state.assert_called_with('Linkedin')
    

