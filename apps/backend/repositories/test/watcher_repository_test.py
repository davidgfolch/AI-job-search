import pytest
from unittest.mock import MagicMock, patch
from repositories.watcher_repository import WatcherRepository

@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_get_match_counts(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    mock_db.fetchAll.return_value = [
        (1, 0, 5),
        (1, 1, 2),
        (2, 0, 3),
    ]

    config_ids = [1, 2]
    results = repo.get_match_counts(config_ids)

    assert results[1] == {"active": 5, "deleted": 2}
    assert results[2] == {"active": 3, "deleted": 0}


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_get_recent_counts(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    mock_db.fetchAll.return_value = [
        (1, 0, 3),
        (1, 1, 1),
        (2, 0, 2),
    ]

    config_ids = [1, 2]
    cutoff = "2023-01-01T00:00:00"
    results = repo.get_recent_counts(config_ids, cutoff)

    assert results[1] == {"new": 3, "removed": 1}
    assert results[2] == {"new": 2, "removed": 0}


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_get_watched_configs(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    mock_db.fetchAll.return_value = [
        (1, '{"search": "python"}'),
        (2, None),
    ]

    results = repo.get_watched_configs()

    assert results == [(1, '{"search": "python"}'), (2, "{}")]


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_invalidate_view(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    repo.invalidate_view(42)

    mock_db.executeAndCommit.assert_called_once_with(
        "DELETE FROM watcher_match WHERE config_id = %s", (42,)
    )


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_invalidate_watcher_view(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    repo.invalidate_watcher_view(42)

    mock_db.executeAndCommit.assert_called_once_with(
        "DELETE FROM watcher_match WHERE config_id = %s", (42,)
    )


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_get_existing_job_ids(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    mock_db.fetchAll.return_value = [(10,), (20,)]

    result = repo.get_existing_job_ids([10, 20, 30])

    assert result == {10, 20}


@patch("repositories.watcher_repository.WatcherRepository.get_db")
def test_get_active_matches_for_jobs(mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db

    mock_db.fetchAll.return_value = [(1, 10), (2, 20)]

    result = repo.get_active_matches_for_jobs([10, 20])

    assert result == [(1, 10), (2, 20)]
