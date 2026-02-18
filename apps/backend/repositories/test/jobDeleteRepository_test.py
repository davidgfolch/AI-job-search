import pytest
from unittest.mock import MagicMock, patch
from repositories.jobDeleteRepository import JobDeleteRepository


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
