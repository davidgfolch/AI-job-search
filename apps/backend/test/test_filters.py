import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app

client = TestClient(app)

def create_mock_db(**kwargs):
    """Helper to create a mock database that supports context manager"""
    mock_db = Mock()
    columns = kwargs.get('columns', ['id', 'title', 'company'])
    data_rows = kwargs.get('fetchAll', [])
    
    def fetch_all_side_effect(query, params=None):
        if "SHOW COLUMNS" in str(query).upper():
            return [(c,) for c in columns]
        return data_rows

    mock_db.count.return_value = kwargs.get('count', 0)
    mock_db.fetchAll.side_effect = fetch_all_side_effect
    mock_db.fetchOne.return_value = kwargs.get('fetchOne', None)
    mock_db.getTableDdlColumnNames.return_value = columns
    mock_db.executeAndCommit.return_value = kwargs.get('executeAndCommit', 1)
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=False)
    return mock_db

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_days_old(mock_get_db):
    """Test listing jobs with days_old filter"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?days_old=7")
    
    assert response.status_code == 200
    
    # Verify the query was constructed with days_old filter
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    assert "DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)" in matched_query
    
    # Check params in the matched call
    matched_call = next((call for call in mock_db.fetchAll.call_args_list if "SELECT" in str(call[0][0])), None)
    if matched_call:
        params = matched_call[0][1]
        assert 7 in params

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_salary(mock_get_db):
    """Test listing jobs with salary regex filter"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?salary=50k")
    
    assert response.status_code == 200
    
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    assert "salary RLIKE %s" in matched_query
    
    matched_call = next((call for call in mock_db.fetchAll.call_args_list if "SELECT" in str(call[0][0])), None)
    if matched_call:
        params = matched_call[0][1]
        assert "50k" in params

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_order(mock_get_db):
    """Test listing jobs with custom order"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?order=salary asc")
    
    assert response.status_code == 200
    
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    assert "ORDER BY salary asc" in matched_query

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_invalid_order(mock_get_db):
    """Test listing jobs with invalid order defaults to created desc"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?order=invalid_col invalid_dir")
    
    assert response.status_code == 200
    
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    # Should fall back to default or partial match. 
    # Our implementation defaults sort_col to "created" if invalid, and sort_dir to "desc" if invalid.
    assert "ORDER BY created desc" in matched_query
