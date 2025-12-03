import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from main import app

client = TestClient(app)

def create_mock_db(**kwargs):
    """Helper to create a mock database that supports context manager"""
    mock_db = Mock()
    mock_db.count.return_value = kwargs.get('count', 0)
    mock_db.fetchAll.return_value = kwargs.get('fetchAll', [])
    mock_db.fetchOne.return_value = kwargs.get('fetchOne', None)
    mock_db.getTableDdlColumnNames.return_value = kwargs.get('columns', ['id', 'title', 'company'])
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
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    params = call_args[0][1]
    
    assert "DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)" in query
    assert 7 in params

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_salary(mock_get_db):
    """Test listing jobs with salary regex filter"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?salary=50k")
    
    assert response.status_code == 200
    
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    params = call_args[0][1]
    
    assert "salary RLIKE %s" in query
    assert "50k" in params

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_order(mock_get_db):
    """Test listing jobs with custom order"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?order=salary asc")
    
    assert response.status_code == 200
    
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    
    assert "ORDER BY salary asc" in query

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_invalid_order(mock_get_db):
    """Test listing jobs with invalid order defaults to created desc"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?order=invalid_col invalid_dir")
    
    assert response.status_code == 200
    
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    
    # Should fall back to default or partial match. 
    # Our implementation defaults sort_col to "created" if invalid, and sort_dir to "desc" if invalid.
    assert "ORDER BY created desc" in query
