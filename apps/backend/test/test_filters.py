import pytest
from unittest.mock import patch

create_mock_db = pytest.create_mock_db

def _request_jobs(client, query_params):
    response = client.get(f"/api/jobs?{query_params}")
    assert response.status_code == 200
    return response

def _get_query_from_mock(mock_db):
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    return next((q for q in queries if "SELECT" in q and "FROM" in q), "")

@pytest.fixture
def mock_db_session():
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    with patch('repositories.jobs_repository.JobsRepository.get_db', return_value=mock_db):
        yield mock_db

def test_list_jobs_with_days_old(mock_db_session, client):
    """Test listing jobs with days_old filter"""
    response = _request_jobs(client, "days_old=7")
    matched_query = _get_query_from_mock(mock_db_session)
    assert "DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)" in matched_query
    # Check params in the matched call
    matched_call = next((call for call in mock_db_session.fetchAll.call_args_list if "SELECT" in str(call[0][0])), None)
    if matched_call:
        params = matched_call[0][1]
        assert 7 in params

def test_list_jobs_with_salary(mock_db_session, client):
    """Test listing jobs with salary regex filter"""
    response = _request_jobs(client, "salary=50k")
    matched_query = _get_query_from_mock(mock_db_session)
    assert "salary RLIKE %s" in matched_query
    matched_call = next((call for call in mock_db_session.fetchAll.call_args_list if "SELECT" in str(call[0][0])), None)
    if matched_call:
        params = matched_call[0][1]
        assert "50k" in params

def test_list_jobs_with_order(mock_db_session, client):
    """Test listing jobs with custom order"""
    response = _request_jobs(client, "order=salary asc")
    matched_query = _get_query_from_mock(mock_db_session)
    assert "ORDER BY salary asc" in matched_query

def test_list_jobs_with_invalid_order(mock_db_session, client):
    """Test listing jobs with invalid order defaults to created desc"""
    response = _request_jobs(client, "order=invalid_col invalid_dir")
    matched_query = _get_query_from_mock(mock_db_session)
    # Should fall back to default or partial match. 
    # Our implementation defaults sort_col to "created" if invalid, and sort_dir to "desc" if invalid.
    assert "ORDER BY created desc" in matched_query
