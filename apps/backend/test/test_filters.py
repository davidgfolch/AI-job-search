import pytest
from unittest.mock import patch

create_mock_db = pytest.create_mock_db

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_days_old(mock_get_db, client):
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
def test_list_jobs_with_salary(mock_get_db, client):
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
def test_list_jobs_with_order(mock_get_db, client):
    """Test listing jobs with custom order"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?order=salary asc")
    
    assert response.status_code == 200
    
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    assert "ORDER BY salary asc" in matched_query

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_invalid_order(mock_get_db, client):
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
