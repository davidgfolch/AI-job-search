import pytest
from unittest.mock import patch, MagicMock

# From jobs_ids_test.py
create_mock_db = pytest.create_mock_db
JOB_COLUMNS = pytest.JOB_COLUMNS

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

# Tests from filters_test.py
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

# Tests from jobs_filters_test.py
@patch('repositories.jobs_repository.JobsRepository.get_db')
@pytest.mark.parametrize("query_param, expected_query_part", [
    ("search=Python", "LIKE"),
    ("status=applied", "`applied` = 1"),
    ("not_status=applied", "`applied` = 0"),
    ("sql_filter=salary > 1000", "(salary > 1000)"),
], ids=["search", "status", "not_status", "sql_filter"])
def test_list_jobs_with_single_filters(mock_get_db, client, query_param, expected_query_part):
    """Test listing jobs with various single filters"""
    mock_db = create_mock_db(
        count=1,
        fetchAll=[(1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None, None)],
        columns=['id', 'title', 'company', 'location', 'salary', 'url', 'markdown', 'web_page', 'created', 'modified', 'merged']
    )
    mock_get_db.return_value = mock_db
    
    response = client.get(f"/api/jobs?{query_param}")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    # Check if any query contains the expected part
    matched = any(expected_query_part in q for q in queries)
    assert matched, f"Expected '{expected_query_part}' in queries: {queries}"

@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_pagination(mock_get_db, client):
    """Test pagination parameters"""
    mock_db = create_mock_db(
        count=50,
        fetchAll=[],
        columns=['id', 'title', 'company']
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?page=2&size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 2
    assert data['size'] == 10
    assert data['total'] == 50

@patch('repositories.jobs_repository.JobsRepository.get_db')
@pytest.mark.parametrize("query_params, expected_conditions", [
    ("flagged=true", ["`flagged` = 1"]),
    ("applied=false", ["`applied` = 0"]),
    ("flagged=true&ai_enriched=true&ignored=false", ["`flagged` = 1", "`ai_enriched` = 1", "`ignored` = 0"]),
    ("search=Python&flagged=true&status=applied", ["LIKE", "`flagged` = 1", "`applied` = 1"]),
], ids=["bool_true", "bool_false", "multiple_bool", "mixed_filters"])
def test_list_jobs_with_combined_filters(mock_get_db, client, query_params, expected_conditions):
    """Test listing jobs with boolean and combined filters"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get(f"/api/jobs?{query_params}")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    for condition in expected_conditions:
        assert condition in matched_query

# Tests from jobs_ids_test.py
@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_by_ids(mock_get_db, client):
    """Test listing jobs filtered by specific IDs"""
    # Create mock DB that checks the query contains "id IN"
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    mock_db.__exit__.return_value = None
    
    # Mock count return
    mock_db.count.return_value = 2
    
    # Mock fetchAll return (jobs) and columns
    mock_db.fetchAll.side_effect = [
        # First call for fetch_jobs
        [
            (1, 'Target Job 1', 'Company A', 'Remote', None, None, None, None, None, None, None),
            (3, 'Target Job 3', 'Company B', 'Remote', None, None, None, None, None, None, None),
        ],
        # Second call for columns
        [(col,) for col in JOB_COLUMNS]
    ]
    
    mock_get_db.return_value = mock_db
    
    # Request with ids param (FastAPI Query param for list usually looks like ?ids=1&ids=3)
    response = client.get("/api/jobs?ids=1&ids=3")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['items']) == 2
    assert data['items'][0]['id'] == 1
    assert data['items'][1]['id'] == 3
    
    # Verify the SQL query generated contained the ID filter
    call_args = mock_db.fetchAll.call_args_list[0]
    query = call_args[0][0]
    params = call_args[0][1]
    
    assert "id IN (%s, %s)" in query
    assert "id IN (%s, %s)" in query
    assert 1 in params
    assert 3 in params

def test_list_jobs_with_created_after(mock_db_session, client):
    """Test listing jobs with created_after filter"""
    cutoff = "2023-01-01T00:00:00"
    response = client.get(f"/api/jobs?created_after={cutoff}")
    assert response.status_code == 200
    
    matched_query = _get_query_from_mock(mock_db_session)
    assert "created > %s" in matched_query
    
    matched_call = next((call for call in mock_db_session.fetchAll.call_args_list if "SELECT" in str(call[0][0])), None)
    if matched_call:
        params = matched_call[0][1]
        assert cutoff in params




