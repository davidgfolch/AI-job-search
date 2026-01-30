import pytest
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.mysqlUtil import MysqlUtil

# We mock MysqlUtil for unit testing
class MockMysqlUtil:
    def __init__(self):
        self.count_result = 0
        self.fetch_all_result = []
        self.fetch_one_result = None
        self.update_called = False
        
    def count(self, query):
        return self.count_result
        
    def fetchAll(self, query):
        return self.fetch_all_result
        
    def fetchOne(self, query, *args):
        return self.fetch_one_result
        
    def updateFromAI(self, query, params):
        self.update_called = True
        
    def executeAndCommit(self, query, params):
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

def test_update_enrichment():
    mock_mysql, repo = mockRepo()
    repo.update_enrichment(1, "100k", "python", "java")
    assert mock_mysql.update_called

def test_get_pending_cv_match_ids():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(10,), (20,)]
    assert repo.get_pending_cv_match_ids(5) == [10, 20]
