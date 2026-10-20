import pytest
from unittest.mock import MagicMock, patch
from repositories.watcher_match_repository import WatcherMatchRepository

@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock


@patch("repositories.watcher_match_repository.WatcherMatchRepository.get_db")
def test_insert_match(mock_get_db, mock_db):
    repo = WatcherMatchRepository()
    mock_get_db.return_value = mock_db

    repo.insert_match(1, 10)
    repo.insert_match(1, 20)

    assert mock_db.executeAndCommit.call_count == 2


@patch("repositories.watcher_match_repository.WatcherMatchRepository.get_db")
def test_insert_tombstone(mock_get_db, mock_db):
    repo = WatcherMatchRepository()
    mock_get_db.return_value = mock_db

    repo.insert_tombstone(1, 10)
    repo.insert_tombstone(1, 20)

    assert mock_db.executeAndCommit.call_count == 2


@patch("repositories.watcher_match_repository.WatcherMatchRepository.get_db")
def test_delete_active_matches_for_jobs(mock_get_db, mock_db):
    repo = WatcherMatchRepository()
    mock_get_db.return_value = mock_db

    repo.delete_active_matches_for_jobs([10, 20])

    mock_db.executeAndCommit.assert_called_once()
    args = mock_db.executeAndCommit.call_args
    assert "deleted = 0" in args[0][0]
    assert args[0][1] == (10, 20)


@patch("repositories.watcher_match_repository.WatcherMatchRepository.get_db")
def test_delete_active_matches_for_jobs_empty(mock_get_db, mock_db):
    repo = WatcherMatchRepository()
    mock_get_db.return_value = mock_db

    repo.delete_active_matches_for_jobs([])

    mock_db.executeAndCommit.assert_not_called()


@patch("repositories.watcher_match_repository.WatcherMatchRepository.get_db")
def test_cleanup_old_rows(mock_get_db, mock_db):
    repo = WatcherMatchRepository()
    mock_get_db.return_value = mock_db
    mock_db.executeAndCommit.return_value = 42

    deleted = repo.cleanup_old_rows(older_than_days=1)

    assert deleted == 42
