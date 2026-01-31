import pytest
from unittest.mock import MagicMock
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.mysqlUtil import MysqlUtil

# We mock MysqlUtil for unit testing
class MockMysqlUtil:
    def __init__(self):
        self.count_result = 0
        self.fetch_all_result = []
        self.fetch_one_result = None
        self.update_called = False
        self.last_query = None
        self.last_params = None
        
    def count(self, query):
        return self.count_result
        
    def fetchAll(self, query):
        return self.fetch_all_result
        
    def fetchOne(self, query, *args):
        return self.fetch_one_result
        
    def updateFromAI(self, query, params):
        self.update_called = True
        self.last_query = query
        self.last_params = params
        
    def executeAndCommit(self, query, params):
        self.last_query = query
        self.last_params = params
        return 1

def mockRepo():
    mock_mysql = MockMysqlUtil()
    repo = AiEnrichRepository(mock_mysql)
    return mock_mysql, repo


def test_count_pending_enrichment():
    mock_mysql, repo = mockRepo()
    mock_mysql.count_result = 5
    assert repo.count_pending_enrichment() == 5

def test_get_pending_enrichment_ids():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(1,), (2,)]
    assert repo.get_pending_enrichment_ids() == [1, 2]

def test_get_job_to_enrich():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_one_result = (1, "Title", "Markdown", "Company")
    assert repo.get_job_to_enrich(1) == (1, "Title", "Markdown", "Company")

def test_get_enrichment_error_id_retry():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(10,)]
    assert repo.get_enrichment_error_id_retry() == 10
    
    mock_mysql.fetch_all_result = []
    assert repo.get_enrichment_error_id_retry() is None

def test_get_job_to_retry():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_one_result = (1, "Title", "MD", "Co")
    assert repo.get_job_to_retry(1) == (1, "Title", "MD", "Co")

def test_update_enrichment():
    mock_mysql, repo = mockRepo()
    repo.update_enrichment(1, "100k", "python", "java")
    assert mock_mysql.update_called
    # Check params structure if needed, but basic call verification is good

def test_update_enrichment_error():
    mock_mysql, repo = mockRepo()
    repo.update_enrichment_error(1, "Error message", is_enrichment=True)
    assert "ai_enrich_error" in mock_mysql.last_query
    
    repo.update_enrichment_error(1, "Error", is_enrichment=False)
    assert "cv_match_percentage" in mock_mysql.last_query

def test_count_pending_cv_match():
    mock_mysql, repo = mockRepo()
    mock_mysql.count_result = 3
    assert repo.count_pending_cv_match() == 3

def test_get_pending_cv_match_ids():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(10,), (20,)]
    assert repo.get_pending_cv_match_ids(5) == [10, 20]

def test_get_job_to_match_cv():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_one_result = (1, "T", "M", "C")
    assert repo.get_job_to_match_cv(1) == (1, "T", "M", "C")

def test_update_cv_match():
    mock_mysql, repo = mockRepo()
    repo.update_cv_match(1, 95)
    assert mock_mysql.update_called
    assert "cv_match_percentage" in mock_mysql.last_query
