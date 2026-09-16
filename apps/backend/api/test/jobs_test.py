import pytest
from unittest.mock import patch, MagicMock

from .jobs_helpers import request_jobs, get_query_from_mock, mock_job_dict

create_mock_db = pytest.create_mock_db
JOB_COLUMNS = pytest.JOB_COLUMNS


@pytest.fixture
def mock_db_session():
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title'])
    with patch('repositories.jobs_repository.JobsRepository.get_db', return_value=mock_db):
        yield mock_db


@pytest.fixture
def mock_jobs_service(client):
    from api.jobs import get_service
    mock_service = MagicMock()
    client.app.dependency_overrides[get_service] = lambda: mock_service
    yield mock_service
    client.app.dependency_overrides.pop(get_service, None)


@pytest.fixture
def mock_watcher_service(client):
    from api.jobs import get_watcher_service
    mock_watcher = MagicMock()
    client.app.dependency_overrides[get_watcher_service] = lambda: mock_watcher
    yield mock_watcher
    client.app.dependency_overrides.pop(get_watcher_service, None)


@pytest.mark.parametrize("query_param, expected_query_part, expected_param_value", [
    ("days_old=7", "DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)", 7),
    ("salary=50k", "salary RLIKE %s", "50k"),
], ids=["days_old", "salary"])
def test_list_jobs_with_regex_date_filters(mock_db_session, client, query_param, expected_query_part, expected_param_value):
    request_jobs(client, query_param)
    assert expected_query_part in get_query_from_mock(mock_db_session)
    calls = [c for c in mock_db_session.fetchAll.call_args_list if "SELECT" in str(c[0][0])]
    assert calls and expected_param_value in calls[0][0][1]


@pytest.mark.parametrize("query_param, expected_order_clause", [
    ("order=salary asc", "ORDER BY salary asc"),
    ("order=invalid_col invalid_dir", "ORDER BY created desc"),
], ids=["valid_order", "invalid_order"])
def test_list_jobs_with_ordering(mock_db_session, client, query_param, expected_order_clause):
    request_jobs(client, query_param)
    assert expected_order_clause in get_query_from_mock(mock_db_session)


@patch('repositories.jobs_repository.JobsRepository.get_db')
@pytest.mark.parametrize("query_param, expected_query_part", [
    ("search=Python", "LIKE"),
    ("status=applied", "`applied` = 1"),
    ("not_status=applied", "`applied` = 0"),
    ("sql_filter=salary > 1000", "(salary > 1000)"),
], ids=["search", "status", "not_status", "sql_filter"])
def test_list_jobs_with_single_filters(mock_get_db, client, query_param, expected_query_part):
    mock_db = create_mock_db(count=1, fetchAll=[(1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None)], columns=['id', 'title', 'company', 'location', 'salary', 'url', 'markdown', 'web_page', 'created', 'modified'])
    mock_get_db.return_value = mock_db
    assert client.get(f"/api/jobs?{query_param}").status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any(expected_query_part in q for q in queries), f"Expected '{expected_query_part}' in queries: {queries}"


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_pagination(mock_get_db, client):
    mock_db = create_mock_db(count=50, fetchAll=[], columns=['id', 'title', 'company'])
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
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    assert client.get(f"/api/jobs?{query_params}").status_code == 200
    matched_query = get_query_from_mock(mock_db)
    for condition in expected_conditions:
        assert condition in matched_query


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_by_ids(mock_get_db, client):
    mock_db = create_mock_db(count=2)
    mock_db.fetchAll.side_effect = [[
        (1, 'Target Job 1', 'Company A', 'Remote', None, None, None, None, None, None),
        (3, 'Target Job 3', 'Company B', 'Remote', None, None, None, None, None, None)],
        [(col,) for col in JOB_COLUMNS]]
    mock_get_db.return_value = mock_db
    response = client.get("/api/jobs?ids=1&ids=3")
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['items']) == 2
    assert data['items'][0]['id'] == 1
    assert data['items'][1]['id'] == 3
    query, params = mock_db.fetchAll.call_args_list[0][0]
    assert "id IN (%s, %s)" in query
    assert 1 in params
    assert 3 in params


def test_list_jobs_with_created_after(mock_db_session, client):
    cutoff = "2023-01-01T00:00:00"
    assert client.get(f"/api/jobs?created_after={cutoff}").status_code == 200
    assert "created > %s" in get_query_from_mock(mock_db_session)
    calls = [c for c in mock_db_session.fetchAll.call_args_list if "SELECT" in str(c[0][0])]
    assert calls and cutoff in calls[0][0][1]


def test_create_job_success(client, mock_jobs_service):
    mock_jobs_service.create_job.return_value = mock_job_dict()
    response = client.post("/api/jobs", json={"title": "Job 1", "company": "Acme"})
    assert response.status_code == 200
    assert response.json()["id"] == 1
    mock_jobs_service.create_job.assert_called_once()


def test_create_job_failure(client, mock_jobs_service):
    mock_jobs_service.create_job.return_value = None
    response = client.post("/api/jobs", json={"title": "Job 1", "company": "Acme"})
    assert response.status_code == 500


def test_get_job_success(client, mock_jobs_service):
    mock_jobs_service.get_job.return_value = mock_job_dict()
    response = client.get("/api/jobs/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_job_not_found(client, mock_jobs_service):
    mock_jobs_service.get_job.return_value = None
    response = client.get("/api/jobs/999")
    assert response.status_code == 404


def test_update_job_success(client, mock_jobs_service):
    mock_jobs_service.update_job.return_value = mock_job_dict()
    response = client.patch("/api/jobs/1", json={"ignored": True})
    assert response.status_code == 200
    assert response.json()["id"] == 1
    mock_jobs_service.update_job.assert_called_once()


def test_update_job_not_found(client, mock_jobs_service):
    mock_jobs_service.update_job.return_value = None
    response = client.patch("/api/jobs/999", json={"ignored": True})
    assert response.status_code == 404


def test_bulk_update_jobs(client, mock_jobs_service):
    mock_jobs_service.bulk_update_jobs.return_value = 3
    response = client.post("/api/jobs/bulk", json={"ids": [1, 2, 3], "update": {"ignored": True}})
    assert response.status_code == 200
    assert response.json() == {"updated": 3}


def test_bulk_delete_jobs(client, mock_jobs_service):
    mock_jobs_service.delete_jobs.return_value = 2
    response = client.post("/api/jobs/bulk/delete", json={"ids": [1, 2]})
    assert response.status_code == 200
    assert response.json() == {"deleted": 2}


@pytest.mark.parametrize("query_params, expected_ids, expected_cutoff", [
    ("config_ids=1,3&from_1=2023-01-01T00:00:00", [1, 3], {1: "2023-01-01T00:00:00"}),
    ("config_ids=2", [2], {}),
], ids=["with_cutoff", "without_cutoff"])
def test_watcher_stats(client, mock_watcher_service, query_params, expected_ids, expected_cutoff):
    mock_watcher_service.get_watcher_stats.return_value = {}
    response = client.get(f"/api/jobs/watcher-stats?{query_params}")
    assert response.status_code == 200
    mock_watcher_service.get_watcher_stats.assert_called_once()
    call_kwargs = mock_watcher_service.get_watcher_stats.call_args[1]
    assert call_kwargs["config_ids"] == expected_ids
    assert call_kwargs["cutoff_map"] == expected_cutoff