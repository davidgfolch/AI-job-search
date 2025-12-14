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

@pytest.mark.parametrize("query_param, expected_query_part, expected_param_value", [
    ("days_old=7", "DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)", 7),
    ("salary=50k", "salary RLIKE %s", "50k"),
], ids=["days_old", "salary"])
def test_list_jobs_with_regex_date_filters(mock_db_session, client, query_param, expected_query_part, expected_param_value):
    """Test listing jobs with date and regex filters"""
    response = _request_jobs(client, query_param)
    matched_query = _get_query_from_mock(mock_db_session)
    assert expected_query_part in matched_query
    
    matched_call = next((call for call in mock_db_session.fetchAll.call_args_list if "SELECT" in str(call[0][0])), None)
    if matched_call:
        params = matched_call[0][1]
        assert expected_param_value in params

@pytest.mark.parametrize("query_param, expected_order_clause", [
    ("order=salary asc", "ORDER BY salary asc"),
    ("order=invalid_col invalid_dir", "ORDER BY created desc"),
], ids=["valid_order", "invalid_order"])
def test_list_jobs_with_ordering(mock_db_session, client, query_param, expected_order_clause):
    """Test listing jobs with custom and invalid ordering"""
    response = _request_jobs(client, query_param)
    matched_query = _get_query_from_mock(mock_db_session)
    assert expected_order_clause in matched_query
