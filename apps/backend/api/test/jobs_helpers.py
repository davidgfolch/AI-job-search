import pytest
from unittest.mock import patch, MagicMock

create_mock_db = pytest.create_mock_db


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
    from api.watcher import get_watcher_service
    mock_watcher = MagicMock()
    client.app.dependency_overrides[get_watcher_service] = lambda: mock_watcher
    yield mock_watcher
    client.app.dependency_overrides.pop(get_watcher_service, None)


def request_jobs(client, query_params):
    response = client.get(f"/api/jobs?{query_params}")
    assert response.status_code == 200
    return response


def get_query_from_mock(mock_db):
    """Return the paged SELECT from wherever the repository issued it."""
    queries = [str(call[0][0]) for call in mock_db.fetchAllWithColumns.call_args_list]
    queries += [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    return next((q for q in queries if "SELECT" in q and "FROM" in q), "")


def mock_job_dict(job_id=1):
    return {
        "id": job_id,
        "title": "Job 1",
        "company": "Acme",
        "created": "2023-01-01T00:00:00",
        "modified": "2023-01-01T00:00:00",
    }
