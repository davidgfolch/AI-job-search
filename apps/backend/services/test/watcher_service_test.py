import pytest
from unittest.mock import MagicMock, patch
from services.watcher_service import WatcherService


@pytest.fixture(autouse=True)
def reset_singleton():
    WatcherService.reset_for_testing()
    yield


@pytest.fixture
def mock_repo():
    return MagicMock()


def test_get_watcher_stats(mock_repo):
    with patch("services.watcher_service.WatcherRepository", return_value=mock_repo):
        service = WatcherService()

        mock_repo.get_match_counts.return_value = {
            1: {"active": 2, "deleted": 1},
            2: {"active": 1, "deleted": 0},
        }
        mock_repo.get_recent_counts.return_value = {
            1: {"new": 1, "removed": 1},
            2: {"new": 1, "removed": 0},
        }

        config_ids = [1, 2]
        cutoff_map = {1: "2023-01-12", 2: "2023-01-01"}

        results = service.get_watcher_stats(config_ids, cutoff_map)

        assert results[1]["total"] == 2
        assert results[1]["new_items"] == 1
        assert results[1]["removed_items"] == 1
        assert results[2]["total"] == 1
        assert results[2]["new_items"] == 1
        assert results[2]["removed_items"] == 0


def test_get_watcher_stats_forwards_each_config_own_cutoff(mock_repo):
    """Every configuration keeps its own cutoff: the map is never collapsed to a single value."""
    with patch("services.watcher_service.WatcherRepository", return_value=mock_repo):
        service = WatcherService()

        mock_repo.get_match_counts.return_value = {
            1: {"active": 2, "deleted": 0},
            2: {"active": 1, "deleted": 0},
        }
        mock_repo.get_recent_counts.return_value = {
            1: {"new": 0, "removed": 0},
            2: {"new": 4, "removed": 0},
        }

        config_ids = [1, 2]
        cutoff_map = {1: "2026-10-21T10:00:00", 2: "2026-10-21T09:00:00"}

        results = service.get_watcher_stats(config_ids, cutoff_map)

        mock_repo.get_recent_counts.assert_called_once_with(config_ids, cutoff_map)
        assert results[1]["new_items"] == 0
        assert results[2]["new_items"] == 4


def test_get_watcher_stats_string_dates(mock_repo):
    with patch("services.watcher_service.WatcherRepository", return_value=mock_repo):
        service = WatcherService()

        mock_repo.get_match_counts.return_value = {1: {"active": 2, "deleted": 0}}
        mock_repo.get_recent_counts.return_value = {1: {"new": 1, "removed": 0}}

        config_ids = [1]
        cutoff_map = {1: "2023-01-12"}

        results = service.get_watcher_stats(config_ids, cutoff_map)

        assert results[1]["total"] == 2
        assert results[1]["new_items"] == 1


def test_get_watcher_stats_error_handling(mock_repo, log_records):
    with patch("services.watcher_service.WatcherRepository", return_value=mock_repo):
        service = WatcherService()

        mock_repo.get_match_counts.side_effect = Exception("DB Error")

        results = service.get_watcher_stats([1])

        assert results[1]["total"] == 0
        assert results[1]["new_items"] == 0
        assert results[1]["removed_items"] == 0
        records = log_records(event="watcher.stats_failed")
        assert len(records) == 1
        assert records[0]["level"] == "error"
        assert records[0]["error"] == "DB Error"
        assert records[0]["config_count"] == 1


def test_get_watcher_stats_timezone_mismatch(mock_repo):
    with patch("services.watcher_service.WatcherRepository", return_value=mock_repo):
        service = WatcherService()

        mock_repo.get_match_counts.return_value = {1: {"active": 1, "deleted": 0}}
        mock_repo.get_recent_counts.return_value = {1: {"new": 0, "removed": 0}}

        config_ids = [1]
        cutoff_map = {1: "2026-02-07T09:00:00.000Z"}

        results = service.get_watcher_stats(config_ids, cutoff_map)

        assert results[1]["new_items"] == 0


def test_get_watcher_stats_naive_local_input(mock_repo):
    with patch("services.watcher_service.WatcherRepository", return_value=mock_repo):
        service = WatcherService()

        mock_repo.get_match_counts.return_value = {1: {"active": 1, "deleted": 0}}
        mock_repo.get_recent_counts.return_value = {1: {"new": 0, "removed": 0}}

        config_ids = [1]
        cutoff_map = {1: "2026-02-07T10:00:00"}

        results = service.get_watcher_stats(config_ids, cutoff_map)

        assert results[1]["new_items"] == 0

        mock_repo.get_recent_counts.return_value = {1: {"new": 1, "removed": 0}}
        results_2 = service.get_watcher_stats(config_ids, cutoff_map)
        assert results_2[1]["new_items"] == 1
