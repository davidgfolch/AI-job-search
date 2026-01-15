import pytest
from unittest.mock import MagicMock, patch
from scrapper.services.IndeedService import IndeedService
from commonlib.mysqlUtil import MysqlUtil
from scrapper.util.persistence_manager import PersistenceManager

@pytest.fixture
def mock_mysql():
    return MagicMock(spec=MysqlUtil)

@pytest.fixture
def mock_persistence_manager():
    return MagicMock(spec=PersistenceManager)

@pytest.fixture
def service(mock_mysql, mock_persistence_manager):
    return IndeedService(mock_mysql, mock_persistence_manager)

class TestIndeedService:
    def test_get_job_id_jk(self, service):
        url = "https://es.indeed.com/viewjob?jk=1234567890&other=param"
        assert service.get_job_id(url) == "1234567890"

    def test_get_job_id_pagead_jk(self, service):
        url = "https://es.indeed.com/pagead/clk?mo=r&ad=...&jk=0987654321&..."
        assert service.get_job_id(url) == "0987654321"

    def test_get_job_id_vjk(self, service):
        url = "https://es.indeed.com/viewjob?vjk=abcdef123456&other=param"
        assert service.get_job_id(url) == "abcdef123456"

    def test_get_job_id_fallback_regex(self, service):
        url = "https://es.indeed.com/something?arg=1&jk=fallback_id_1"
        assert service.get_job_id(url) == "fallback_id_1"

    def test_get_job_id_fallback_hash(self, service):
        # When no jk or vjk is present
        url = "https://es.indeed.com/no-id"
        # The service falls back to MD5 hash
        import hashlib
        expected_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        assert service.get_job_id(url) == expected_hash

    def test_post_process_markdown(self, service):
        md = "Some text with [link](/ofertas-trabajo/id) and \\- escaped chars"
        processed = service.post_process_markdown(md)
        assert "[link]" not in processed # link should be removed/replaced by text
        assert "\\-" not in processed
        assert "-" in processed

    def test_update_state(self, service, mock_persistence_manager):
        service.update_state("java", 2)
        mock_persistence_manager.update_state.assert_called_with("Indeed", "java", 2)

    def test_job_exists_in_db(self, service, mock_mysql):
        url = "https://es.indeed.com/viewjob?jk=123"
        mock_mysql.fetchOne.return_value = (1,)
        id, exists = service.job_exists_in_db(url)
        assert id == "123"
        assert exists is True
        
        mock_mysql.fetchOne.return_value = None
        id, exists = service.job_exists_in_db(url)
        assert exists is False

    @patch("scrapper.services.IndeedService.htmlToMarkdown")
    @patch("scrapper.services.IndeedService.validate")
    @patch("scrapper.services.IndeedService.mergeDuplicatedJobs")
    @patch("scrapper.services.IndeedService.getSelect")
    def test_process_job_new(self, mock_getSelect, mock_merge, mock_validate, mock_html2md, service, mock_mysql):
        mock_html2md.return_value = "markdown"
        mock_validate.return_value = True
        mock_mysql.fetchOne.return_value = None # Job not in DB
        mock_mysql.insert.return_value = 100 # Inserted ID
        
        result = service.process_job("Title", "Company", "Loc", "http://url?jk=1", "html", False)
        
        assert result is True
        mock_mysql.insert.assert_called()
        mock_merge.assert_called()

    @patch("scrapper.services.IndeedService.htmlToMarkdown")
    def test_process_job_exists(self, mock_html2md, service, mock_mysql):
        mock_html2md.return_value = "markdown"
        mock_mysql.fetchOne.return_value = (1,) # Job exists
        
        result = service.process_job("Title", "Company", "Loc", "http://url?jk=1", "html", False)
        
        assert result is True
        mock_mysql.insert.assert_not_called()

    @patch("scrapper.services.IndeedService.htmlToMarkdown")
    @patch("scrapper.services.IndeedService.validate")
    def test_process_job_invalid(self, mock_validate, mock_html2md, service, mock_mysql):
        mock_html2md.return_value = "markdown"
        mock_mysql.fetchOne.return_value = None
        mock_validate.return_value = False
        
        result = service.process_job("Title", "Company", "Loc", "http://url?jk=1", "html", False)
        
        assert result is False
