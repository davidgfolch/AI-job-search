import pytest
from unittest.mock import MagicMock
from services.jobSnapshotService import JobSnapshotService
from commonlib.jobSnapshotRepository import JobSnapshotRepository


@pytest.fixture
def mock_repo():
    return MagicMock(spec=JobSnapshotRepository)


@pytest.fixture
def service(mock_repo):
    service = JobSnapshotService()
    service.repo = mock_repo
    return service


def test_create_snapshot_from_job(service, mock_repo):
    job_data = {
        "jobId": "test-123",
        "web_page": "linkedin",
        "created": "2023-01-01",
        "title": "Software Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "salary": "100k",
        "applied": True,
        "discarded": False,
        "interview": False,
        "interview_rh": False,
        "interview_tech": False,
        "interview_technical_test": False,
    }
    mock_repo.save_snapshot.return_value = 1

    result = service.create_snapshot_from_job(job_data, "APPLIED")

    assert result == 1
    mock_repo.save_snapshot.assert_called_once()
