import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from commonlib.jobSnapshotRepository import JobSnapshotRepository


@pytest.fixture
def mock_mysql():
    return MagicMock()


@pytest.fixture
def repo(mock_mysql):
    return JobSnapshotRepository(mock_mysql)


def test_save_snapshot(mock_mysql):
    repo = JobSnapshotRepository(mock_mysql)
    mock_mysql.executeAndCommit.return_value = 1
    result = repo.save_snapshot(
        job_id="test-123", platform="linkedin", original_created_at=datetime.now(),
        snapshot_reason="DELETED", title="SE", company="Corp", location="Remote",
        salary="100k", applied=True, discarded=False, interview=False,
        interview_rh=False, interview_tech=False, interview_technical_test=False, web_page="linkedin",
    )
    assert result == 1
    mock_mysql.executeAndCommit.assert_called_once()


def test_get_snapshots_by_date_range(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = [(1, "job-1")]
    result = repo.get_snapshots_by_date_range(datetime(2024, 1, 1), datetime(2024, 12, 31))
    assert len(result) == 1
    mock_mysql.fetchAll.assert_called_once()


def test_get_snapshots_by_reason(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = [(1, "job-1")]
    result = repo.get_snapshots_by_reason("DELETED")
    assert len(result) == 1


def test_get_snapshots_by_platform(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = [(1, "job-1")]
    result = repo.get_snapshots_by_platform("linkedin")
    assert len(result) == 1


def test_count_snapshots_by_reason_with_rows(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = [(5,)]
    result = repo.count_snapshots_by_reason("DELETED")
    assert result == 5


def test_count_snapshots_by_reason_empty(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = []
    result = repo.count_snapshots_by_reason("DELETED")
    assert result == 0


def test_count_snapshots_by_platform_with_rows(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = [(10,)]
    result = repo.count_snapshots_by_platform("linkedin")
    assert result == 10


def test_count_snapshots_by_platform_empty(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = []
    result = repo.count_snapshots_by_platform("linkedin")
    assert result == 0


def test_get_all_snapshots(repo, mock_mysql):
    mock_mysql.fetchAll.return_value = [(1,), (2,)]
    result = repo.get_all_snapshots(limit=100, offset=0)
    assert len(result) == 2


def test_delete_snapshots_older_than(repo, mock_mysql):
    mock_mysql.executeAndCommit.return_value = 3
    result = repo.delete_snapshots_older_than(30)
    assert result == 3


def test_build_snapshot_query_and_params():
    job_data = {
        "jobId": "j1", "web_page": "linkedin", "created": datetime.now(),
        "title": "SE", "company": "Corp", "location": "R", "salary": "50k",
        "applied": True, "discarded": False, "interview": True,
        "interview_rh": False, "interview_tech": False, "interview_technical_test": False,
    }
    query, params = JobSnapshotRepository.build_snapshot_query_and_params(job_data, "TEST")
    assert "INSERT INTO job_snapshots" in query
    assert params["job_id"] == "j1"
    assert params["snapshot_reason"] == "TEST"
    assert params["applied"] is True
    assert params["interview"] is True


def test_build_snapshot_query_empty_job():
    query, params = JobSnapshotRepository.build_snapshot_query_and_params({}, "REASON")
    assert params["job_id"] is None
    assert params["applied"] is False


def test_default_mysql_creates_instance():
    with patch("commonlib.jobSnapshotRepository.MysqlUtil") as mock_mysql_cls:
        repo = JobSnapshotRepository()
        mock_mysql_cls.assert_called_once()
