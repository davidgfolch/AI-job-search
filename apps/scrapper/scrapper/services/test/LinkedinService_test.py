import pytest
from unittest.mock import MagicMock, patch
from commonlib.sql.mysqlUtil import MysqlUtil
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

    def test_print_job_logs_lengths_not_blobs(self, service):
        with patch('scrapper.services.LinkedinService.logger') as log:
            service.print_job('T', 'C', 'L', 'U', 123, '<h1>x</h1>', 'MD')
        log.debug.assert_called_once_with('linkedin.job.already_exists', job_id=123, title='T', company='C', location='L', url='U', html_length=10, markdown_length=2)

    def test_update_job_logs_event(self, service, mock_mysql):
        with patch('scrapper.services.LinkedinService.logger') as log:
            service.update_job(123, 'T', 'C', 'L', 'U', 'H', 'MD', False)
        log.info.assert_called_once_with('linkedin.job.updated', job_id=123)
        mock_mysql.executeAndCommit.assert_called_once()

    def test_process_job_logs_inserted_and_duplicated(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.LinkedinService.find_last_duplicated', return_value=77), \
             patch('scrapper.services.LinkedinService.logger') as log:
            mock_mysql.jobExists.return_value = False
            mock_mysql.insert.return_value = 5
            service.process_job("T", "C", "L", "https://www.linkedin.com/jobs/view/9/", "H", False, False)
        events = {c.args[0]: c.kwargs for c in log.debug.call_args_list + log.info.call_args_list}
        assert events['linkedin.job.inserted'] == {'job_id': 9, 'insert_id': 5}
        assert events['linkedin.job.duplicated'] == {'job_id': 9, 'duplicated_id': 77}

    def test_process_job_logs_scraped_fields(self, service, mock_mysql):
        with patch('scrapper.core.baseScrapper.validate', return_value=True), \
             patch('scrapper.core.baseScrapper.htmlToMarkdown', return_value="MD"), \
             patch('scrapper.services.LinkedinService.find_last_duplicated', return_value=None), \
             patch('scrapper.services.LinkedinService.logger') as log:
            mock_mysql.jobExists.return_value = False
            mock_mysql.insert.return_value = 1
            service.process_job("T", "C", "L", "https://www.linkedin.com/jobs/view/9/", "H", False, True)
        log.debug.assert_any_call('linkedin.job.scraped', job_id=9, title='T', company='C', location='L', easy_apply=True)
