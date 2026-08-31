import pytest
from unittest.mock import MagicMock, patch
from repositories.jobDeleteRepository import JobDeleteRepository
from commonlib.test.db_mock_util import create_mock_db


@pytest.fixture
def mock_mysql():
    return MagicMock()


def test_delete_jobs_by_ids():
    repo = JobDeleteRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.executeAndCommit.return_value = 3

        result = repo.delete_jobs_by_ids([1, 2, 3])

        assert result == 3
        mock_db.executeAndCommit.assert_called_once()


def test_delete_jobs_by_ids_empty():
    repo = JobDeleteRepository()
    assert repo.delete_jobs_by_ids([]) == 0


def test_delete_jobs_by_filter():
    repo = JobDeleteRepository()
    mock_db = create_mock_db(executeAndCommit=5)
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.delete_jobs_by_filter(["status = %s", "company = %s"], ["applied", "Acme"])

    assert result == 5
    query = mock_db.executeAndCommit.call_args[0][0]
    assert "DELETE FROM jobs" in query
    assert "status = %s" in query


def test_delete_jobs_with_snapshots():
    repo = JobDeleteRepository()
    mock_db = create_mock_db(fetchAll=[(1, "Job 1"), (2, "Job 2")])
    mock_db.executeAllAndCommit.return_value = 2
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.delete_jobs_with_snapshots(
            ["status = %s"],
            ["applied"],
            [("INSERT INTO snapshots ...", ["p1"]), ("INSERT INTO snapshots2 ...", ["p2"])],
        )

    assert result == 2
    assert mock_db.executeAllAndCommit.call_count == 1
    queries = mock_db.executeAllAndCommit.call_args[0][0]
    assert len(queries) == 3
    assert "DELETE FROM jobs" in queries[2]["query"]


def test_get_jobs_by_filter():
    repo = JobDeleteRepository()
    mock_db = create_mock_db(fetchAll=[(1, "Job 1"), (2, "Job 2")])
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.get_jobs_by_filter(["1=1"], [])

    assert len(result) == 2
    assert result[0]["id"] == 1


def test_update_jobs_by_ids():
    repo = JobDeleteRepository()
    mock_db = create_mock_db(executeAndCommit=2)
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_jobs_by_ids([1, 2], {"ignored": True})

    assert result == 2
    query = mock_db.executeAndCommit.call_args[0][0]
    assert "UPDATE jobs SET" in query
    assert "id IN (%s, %s)" in query


def test_update_jobs_by_ids_empty():
    repo = JobDeleteRepository()
    mock_db = create_mock_db()
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_jobs_by_ids([], {"ignored": True})

    assert result == 0
    mock_db.executeAndCommit.assert_not_called()


def test_update_jobs_by_filter():
    repo = JobDeleteRepository()
    mock_db = create_mock_db(executeAndCommit=7)
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_jobs_by_filter(["1=1"], [], {"ignored": True})

    assert result == 7
    query = mock_db.executeAndCommit.call_args[0][0]
    assert "UPDATE jobs SET" in query


def test_update_jobs_by_filter_empty():
    repo = JobDeleteRepository()
    mock_db = create_mock_db()
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_jobs_by_filter(["1=1"], [], {})

    assert result == 0
    mock_db.executeAndCommit.assert_not_called()
