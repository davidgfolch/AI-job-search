import pytest
from unittest.mock import MagicMock
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from commonlib.sql.mysqlUtil import MysqlUtil

# We mock MysqlUtil for unit testing
class MockMysqlUtil:
    def __init__(self):
        self.count_result = 0
        self.fetch_all_result = []
        self.configs_result = []
        self.priority_result = []
        self.fetch_one_result = None
        self.update_called = False
        self.updates = []
        self.fetch_all_calls = []
        self.last_query = None
        self.last_params = None
        
    def count(self, query):
        self.last_query = query
        return self.count_result
        
    def fetchAll(self, query, params=None):
        self.last_query = query
        self.last_params = params
        self.fetch_all_calls.append((query, params))
        if "filter_configurations" in query:
            return self.configs_result
        if "created DESC, id DESC" in query:
            return self.priority_result
        return self.fetch_all_result
        
    def fetchOne(self, query, *args):
        return self.fetch_one_result
        
    def updateFromAI(self, query, params):
        self.update_called = True
        self.updates.append((query, params))
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
    assert "ai_enrich_error" in mock_mysql.last_query

def test_get_pending_enrichment_ids():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(1,), (2,)]
    assert repo.get_pending_enrichment_ids() == [1, 2]
    assert "ai_enrich_error" in mock_mysql.last_query


def test_get_pending_enrichment_ids_priority_first_and_deduped():
    mock_mysql, repo = mockRepo()
    mock_mysql.configs_result = [(1, "Python", '{"search": "python"}')]
    mock_mysql.priority_result = [(5,), (1,)]
    mock_mysql.fetch_all_result = [(1,), (2,), (3,)]
    assert repo.get_pending_enrichment_ids() == [5, 1, 2, 3]


def test_get_pending_enrichment_ids_priority_excludes_ai_enriched_filter():
    mock_mysql, repo = mockRepo()
    mock_mysql.configs_result = [(1, "Backend", '{"ai_enriched": true, "applied": true}')]
    repo.get_pending_enrichment_ids()
    match_query = next(q for q, _ in mock_mysql.fetch_all_calls if "created DESC, id DESC" in q)
    assert "`ai_enriched` =" not in match_query
    assert "`applied` = 1" in match_query


def test_config_for_job_exposes_priority_config():
    mock_mysql, repo = mockRepo()
    mock_mysql.configs_result = [(1, "Python", '{}')]
    mock_mysql.priority_result = [(5,)]
    mock_mysql.fetch_all_result = [(5,), (2,)]
    assert repo.get_pending_enrichment_ids() == [5, 2]
    assert repo.config_for_job(5) == "Python"
    assert repo.config_for_job(2) is None

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
    repo.update_enrichment(1, "100k", "python", "java", "REMOTE")
    assert mock_mysql.update_called
    assert "COALESCE" in mock_mysql.last_query
    assert mock_mysql.last_params[-2] == "REMOTE"

def test_update_enrichment_error():
    mock_mysql, repo = mockRepo()
    repo.update_enrichment_error(1, "Error message", is_enrichment=True)
    assert "ai_enrich_error" in mock_mysql.last_query
    assert mock_mysql.last_params["ai_enriched"] is False
    
    repo.update_enrichment_error(1, "Error", is_enrichment=False)
    assert "cv_match_percentage" in mock_mysql.last_query

def test_update_unspecified_company():
    mock_mysql, repo = mockRepo()
    repo.update_unspecified_company(1, "Tech Corp")
    assert mock_mysql.update_called
    assert "TRIM(company)=''" in mock_mysql.last_query
    assert f"'{UNSPECIFIED_COMPANY}'" in mock_mysql.last_query
    assert mock_mysql.last_params == ("Tech Corp", 1)

def test_update_unspecified_company_truncates():
    mock_mysql, repo = mockRepo()
    repo.update_unspecified_company(1, "x" * 300)
    assert len(mock_mysql.last_params[0]) == 200
    assert mock_mysql.last_params[0].endswith("[...]")

def test_update_unspecified_company_ignores_blank():
    mock_mysql, repo = mockRepo()
    repo.update_unspecified_company(1, "   ")
    assert mock_mysql.last_params == (None, 1)

def test_refresh_duplicated_of():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(42,)]
    repo.refresh_duplicated_of(1, "Title", "Tech Corp")
    assert mock_mysql.updates[-1][1] == (42, 1)
    assert "duplicated_id IS NULL" in mock_mysql.updates[-1][0]

def test_refresh_duplicated_of_excludes_itself():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = [(42,)]
    repo.refresh_duplicated_of(7, "Title", "Tech Corp")
    query, params = mock_mysql.fetch_all_calls[0]
    assert "id != %s" in query
    assert params == ["Title", "Tech Corp", 7]

def test_refresh_duplicated_of_no_match():
    mock_mysql, repo = mockRepo()
    mock_mysql.fetch_all_result = []
    repo.refresh_duplicated_of(1, "Title", "Tech Corp")
    assert mock_mysql.update_called is False

def test_refresh_duplicated_of_unspecified_company():
    mock_mysql, repo = mockRepo()
    assert repo.refresh_duplicated_of(1, "Title", UNSPECIFIED_COMPANY) is None
    assert mock_mysql.fetch_all_calls == []
    assert mock_mysql.updates == []

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
