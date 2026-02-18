import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from commonlib.jobSnapshotRepository import JobSnapshotRepository


@pytest.fixture
def mock_mysql():
    return MagicMock()


def test_save_snapshot(mock_mysql):
    repo = JobSnapshotRepository(mock_mysql)
    mock_mysql.executeAndCommit.return_value = 1

    result = repo.save_snapshot(
        job_id="test-123",
        platform="linkedin",
        original_created_at=datetime.now(),
        snapshot_reason="DELETED",
        title="Software Engineer",
        company="Test Corp",
        location="Remote",
        salary="100k",
        applied=True,
        discarded=False,
        interview=False,
        interview_rh=False,
        interview_tech=False,
        interview_technical_test=False,
        web_page="linkedin",
    )

    assert result == 1
    mock_mysql.executeAndCommit.assert_called_once()


def test_get_snapshots_by_reason(mock_mysql):
    repo = JobSnapshotRepository(mock_mysql)
    mock_mysql.fetchAll.return_value = [
        (
            1,
            "test-123",
            "linkedin",
            datetime.now(),
            datetime.now(),
            "DELETED",
            "Software Engineer",
            "Test Corp",
            "Remote",
            "100k",
            1,
            0,
            0,
            0,
            0,
            0,
            "linkedin",
        )
    ]

    result = repo.get_snapshots_by_reason("DELETED")

    assert len(result) == 1
    mock_mysql.fetchAll.assert_called_once()
