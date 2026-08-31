import pytest
from unittest.mock import MagicMock, patch
from services.jobSnapshotService import JobSnapshotService
from commonlib.jobSnapshotRepository import JobSnapshotRepository


@pytest.fixture
def mock_repo():
    return MagicMock(spec=JobSnapshotRepository)


@pytest.fixture
def service(mock_repo):
    with patch(
        "services.jobSnapshotService.JobSnapshotRepository", return_value=mock_repo
    ):
        service = JobSnapshotService()
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


def test_snapshot_before_delete(service, mock_repo):
    result = service.snapshot_before_delete({"jobId": "1"})
    assert result == mock_repo.save_snapshot.return_value
    mock_repo.save_snapshot.assert_called_once()
    assert mock_repo.save_snapshot.call_args[1]["snapshot_reason"] == "DELETED"


def test_snapshot_on_applied(service, mock_repo):
    service.snapshot_on_applied({"jobId": "1"})
    assert mock_repo.save_snapshot.call_args[1]["snapshot_reason"] == "APPLIED"


def test_snapshot_on_interview(service, mock_repo):
    service.snapshot_on_interview({"jobId": "1"})
    assert mock_repo.save_snapshot.call_args[1]["snapshot_reason"] == "INTERVIEW"


def test_snapshot_on_discarded(service, mock_repo):
    service.snapshot_on_discarded({"jobId": "1"})
    assert mock_repo.save_snapshot.call_args[1]["snapshot_reason"] == "DISCARDED"


@pytest.mark.parametrize(
    "new_data,old_applied,old_discarded,old_interview,expected_reason",
    [
        ({"applied": True}, False, False, False, "APPLIED"),
        ({"discarded": True}, False, False, False, "DISCARDED"),
        ({"interview": True}, False, False, False, "INTERVIEW"),
        ({"interview_rh": True}, False, False, False, "INTERVIEW"),
        ({"interview_tech": True}, False, False, False, "INTERVIEW"),
        ({"interview_technical_test": True}, False, False, False, "INTERVIEW"),
        ({"applied": True}, True, False, False, None),
        ({"applied": False}, False, False, False, None),
    ],
)
def test_maybe_create_snapshot_on_update(
    service, mock_repo, new_data, old_applied, old_discarded, old_interview, expected_reason
):
    old_job = {
        "applied": old_applied,
        "discarded": old_discarded,
        "interview": old_interview,
        "interview_rh": old_interview,
        "interview_tech": old_interview,
        "interview_technical_test": old_interview,
    }
    service.maybe_create_snapshot_on_update(old_job, new_data)
    if expected_reason is None:
        mock_repo.save_snapshot.assert_not_called()
    else:
        assert mock_repo.save_snapshot.call_args[1]["snapshot_reason"] == expected_reason


def test_get_snapshots_by_date_range(service, mock_repo):
    service.get_snapshots_by_date_range("2023-01-01", "2023-01-31")
    mock_repo.get_snapshots_by_date_range.assert_called_once_with("2023-01-01", "2023-01-31")


def test_get_snapshots_by_reason(service, mock_repo):
    service.get_snapshots_by_reason("APPLIED")
    mock_repo.get_snapshots_by_reason.assert_called_once_with("APPLIED")


def test_get_snapshots_by_platform(service, mock_repo):
    service.get_snapshots_by_platform("linkedin")
    mock_repo.get_snapshots_by_platform.assert_called_once_with("linkedin")


def test_get_all_snapshots(service, mock_repo):
    service.get_all_snapshots(limit=500, offset=10)
    mock_repo.get_all_snapshots.assert_called_once_with(500, 10)
