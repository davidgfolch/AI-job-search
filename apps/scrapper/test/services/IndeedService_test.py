import pytest
from unittest.mock import MagicMock
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
