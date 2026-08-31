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
        fetchAll=[(1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None)],
        columns=['id', 'title', 'company', 'location', 'salary', 'url', 'markdown', 'web_page', 'created', 'modified']
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
    ("duplicated=true", ["duplicated_id IS NOT NULL"]),
    ("duplicated=false", ["duplicated_id IS NULL"]),
], ids=["bool_true", "bool_false", "multiple_bool", "mixed_filters", "duplicated_true", "duplicated_false"])
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
            (1, 'Target Job 1', 'Company A', 'Remote', None, None, None, None, None, None),
            (3, 'Target Job 3', 'Company B', 'Remote', None, None, None, None, None, None),
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


def _mock_job_dict(job_id=1):
    return {
        "id": job_id,
        "title": "Job 1",
        "company": "Acme",
        "created": "2023-01-01T00:00:00",
        "modified": "2023-01-01T00:00:00",
    }


def test_create_job_success(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.create_job.return_value = _mock_job_dict()
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.post("/api/jobs", json={"title": "Job 1", "company": "Acme"})
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 200
    assert response.json()["id"] == 1
    mock_service.create_job.assert_called_once()


def test_create_job_failure(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.create_job.return_value = None
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.post("/api/jobs", json={"title": "Job 1", "company": "Acme"})
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 500


def test_get_job_success(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.get_job.return_value = _mock_job_dict()
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.get("/api/jobs/1")
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_job_not_found(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.get_job.return_value = None
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.get("/api/jobs/999")
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 404


def test_update_job_success(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.update_job.return_value = _mock_job_dict()
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.patch("/api/jobs/1", json={"ignored": True})
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 200
    assert response.json()["id"] == 1
    mock_service.update_job.assert_called_once()


def test_update_job_not_found(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.update_job.return_value = None
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.patch("/api/jobs/999", json={"ignored": True})
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 404


def test_bulk_update_jobs(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.bulk_update_jobs.return_value = 3
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.post(
            "/api/jobs/bulk", json={"ids": [1, 2, 3], "update": {"ignored": True}}
        )
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 200
    assert response.json() == {"updated": 3}


def test_bulk_delete_jobs(client):
    from api.jobs import get_service

    mock_service = MagicMock()
    mock_service.delete_jobs.return_value = 2
    client.app.dependency_overrides[get_service] = lambda: mock_service
    try:
        response = client.post("/api/jobs/bulk/delete", json={"ids": [1, 2]})
    finally:
        client.app.dependency_overrides.pop(get_service, None)

    assert response.status_code == 200
    assert response.json() == {"deleted": 2}


def test_watcher_stats(client):
    from api.jobs import get_watcher_service

    mock_watcher = MagicMock()
    mock_watcher.get_watcher_stats.return_value = {1: {"total": 5, "new_items": 2}}
    client.app.dependency_overrides[get_watcher_service] = lambda: mock_watcher
    try:
        response = client.get("/api/jobs/watcher-stats?config_ids=1,3&from_1=2023-01-01T00:00:00")
    finally:
        client.app.dependency_overrides.pop(get_watcher_service, None)

    assert response.status_code == 200
    mock_watcher.get_watcher_stats.assert_called_once()
    call_kwargs = mock_watcher.get_watcher_stats.call_args[1]
    assert call_kwargs["config_ids"] == [1, 3]
    assert call_kwargs["cutoff_map"] == {1: "2023-01-01T00:00:00"}


def test_watcher_stats_without_cutoff(client):
    from api.jobs import get_watcher_service

    mock_watcher = MagicMock()
    mock_watcher.get_watcher_stats.return_value = {}
    client.app.dependency_overrides[get_watcher_service] = lambda: mock_watcher
    try:
        response = client.get("/api/jobs/watcher-stats?config_ids=2")
    finally:
        client.app.dependency_overrides.pop(get_watcher_service, None)

    assert response.status_code == 200
    mock_watcher.get_watcher_stats.assert_called_once()
    call_kwargs = mock_watcher.get_watcher_stats.call_args[1]
    assert call_kwargs["config_ids"] == [2]
    assert call_kwargs["cutoff_map"] == {}




