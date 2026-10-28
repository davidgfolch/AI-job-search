from unittest.mock import MagicMock, call, patch

import pytest

from services.watcher_matcher import WatcherMatcher

from .watcher_matcher_mocks import APPLIED_CONFIG, PYTHON_CONFIG, event_kwargs, event_names, wire_match


@pytest.fixture(autouse=True)
def reset_singleton():
    WatcherMatcher.reset_for_testing()
    yield


@pytest.fixture
def mock_repos():
    """Mock both WatcherRepository (reads) and WatcherMatchRepository (writes)."""
    with patch("services.watcher_matcher.WatcherRepository") as mock_repo_cls, patch("services.watcher_matcher.WatcherMatchRepository") as mock_match_repo_cls:
        mock_repo = MagicMock()
        mock_match_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_match_repo_cls.return_value = mock_match_repo
        yield mock_repo, mock_match_repo


@pytest.fixture
def sut(mock_repos):
    return WatcherMatcher()


def test_process_pending_matches_pending_jobs(sut, mock_repos):
    """Pending job ids are matched against each watched filter config."""
    mock_repo, mock_match_repo = mock_repos
    mock_repo.get_watched_configs.return_value = [PYTHON_CONFIG, APPLIED_CONFIG]
    mock_repo.get_existing_job_ids.return_value = {10, 20}
    wire_match(mock_repo, {1: [10], 2: [20]})

    sut.add_pending_ids([10, 20, 30])
    sut._process_pending()

    assert mock_match_repo.insert_match.call_args_list == [call(1, 10), call(2, 20)]


def test_process_pending_deleted_job_produces_tombstone(sut, mock_repos):
    """Deleted job: active matches removed, tombstone inserted."""
    mock_repo, mock_match_repo = mock_repos
    mock_repo.get_watched_configs.return_value = [PYTHON_CONFIG]
    mock_repo.get_existing_job_ids.return_value = set()
    mock_repo.get_active_matches_for_jobs.return_value = [(1, 99)]

    sut.add_pending_ids([99])
    sut._process_pending()

    mock_match_repo.delete_active_matches_for_jobs.assert_called_once_with([99])
    mock_match_repo.insert_tombstone.assert_called_once_with(1, 99)


def test_process_pending_no_configs(sut, mock_repos):
    """If no watched configs, process_pending should be a no-op."""
    mock_repo, mock_match_repo = mock_repos
    mock_repo.get_watched_configs.return_value = []

    sut.add_pending_ids([1, 2, 3])
    sut._process_pending()

    mock_match_repo.insert_match.assert_not_called()
    mock_match_repo.insert_tombstone.assert_not_called()


def test_process_pending_empty_pending(sut, mock_repos):
    """If no pending IDs, process_pending should be a no-op."""
    mock_repo, mock_match_repo = mock_repos
    mock_repo.get_recently_enriched_ids.return_value = []

    sut._process_pending()

    mock_repo.get_watched_configs.assert_not_called()
    mock_match_repo.insert_match.assert_not_called()


def test_handle_deleted_jobs_inserts_tombstones(sut, mock_repos):
    """_handle_deleted_jobs inserts a tombstone per active match of a deleted job."""
    mock_repo, mock_match_repo = mock_repos
    mock_repo.get_active_matches_for_jobs.return_value = [(1, 5), (2, 5)]

    sut._handle_deleted_jobs({5})

    mock_match_repo.delete_active_matches_for_jobs.assert_called_once_with([5])
    assert mock_match_repo.insert_tombstone.call_args_list == [call(1, 5), call(2, 5)]


def test_handle_deleted_jobs_empty(sut, mock_repos):
    """_handle_deleted_jobs with empty set is a no-op."""
    mock_repo, mock_match_repo = mock_repos

    sut._handle_deleted_jobs(set())

    mock_repo.get_active_matches_for_jobs.assert_not_called()
    mock_match_repo.insert_tombstone.assert_not_called()


def test_match_existing_jobs_inserts_matches(sut, mock_repos):
    """_match_existing_jobs runs filter SQL against existing jobs and inserts matches."""
    mock_repo, mock_match_repo = mock_repos
    mock_repo.match_jobs_against_config.return_value = [10, 20]

    sut._match_existing_jobs({10, 20, 30}, [PYTHON_CONFIG])

    config_id, where_part, job_ids = mock_repo.match_jobs_against_config.call_args[0]
    assert (config_id, job_ids) == (1, [10, 20, 30])
    assert isinstance(where_part, str) and where_part
    assert mock_match_repo.insert_match.call_args_list == [call(1, 10), call(1, 20)]


def test_match_existing_jobs_empty(sut, mock_repos):
    """_match_existing_jobs with empty set is a no-op."""
    mock_repo, mock_match_repo = mock_repos

    sut._match_existing_jobs(set(), [PYTHON_CONFIG])

    mock_repo.match_jobs_against_config.assert_not_called()
    mock_match_repo.insert_match.assert_not_called()


def test_match_config_omits_sql_from_info_record(sut, mock_repos):
    """The info record carries ids and counts only; the SQL lives in the debug record."""
    mock_repo, _ = mock_repos
    mock_repo.match_jobs_against_config.return_value = [10]

    with patch("services.watcher_matcher.logger") as mock_logger:
        sut._match_existing_jobs({10}, [PYTHON_CONFIG])

    assert event_kwargs(mock_logger, "info", "watcher.match_config") == [{"config_id": 1, "matched": 1, "matched_ids": [10]}]
    debug_kwargs = event_kwargs(mock_logger, "debug", "watcher.match_config_query")
    assert len(debug_kwargs) == 1
    assert debug_kwargs[0]["config_id"] == 1
    assert debug_kwargs[0]["filters"] == {"search": "python"}
    assert "where" in debug_kwargs[0]


def test_match_config_not_logged_without_matches(sut, mock_repos):
    """A config that matched nothing produces no info record, only the debug one."""
    mock_repo, _ = mock_repos
    mock_repo.match_jobs_against_config.return_value = []

    with patch("services.watcher_matcher.logger") as mock_logger:
        sut._match_existing_jobs({10}, [PYTHON_CONFIG])

    assert "watcher.match_config" not in event_names(mock_logger, "info")
    assert "watcher.match_config_query" in event_names(mock_logger, "debug")


def test_process_pending_logs_count_without_ids(sut, mock_repos):
    """The tick record carries the count; the id list is debug-only."""
    mock_repo, _ = mock_repos
    mock_repo.get_watched_configs.return_value = []
    sut.add_pending_ids([10, 20])

    with patch("services.watcher_matcher.logger") as mock_logger:
        sut._process_pending()

    assert event_kwargs(mock_logger, "info", "watcher.process_pending") == [{"count": 2}]
    assert event_kwargs(mock_logger, "debug", "watcher.process_pending_ids") == [{"pending_ids": [10, 20]}]


@pytest.mark.parametrize("filters_json, expected", [
    pytest.param('{"search": "python"}', {"search": "python"}, id="valid_json"),
    pytest.param("not-json", {}, id="invalid_json"),
    pytest.param(None, {}, id="none"),
])
def test_parse_filters(filters_json, expected):
    """_parse_filters parses JSON strings and falls back to {} for None or bad JSON."""
    assert WatcherMatcher._parse_filters(filters_json) == expected


def test_singleton_repeated_access_preserves_pending_ids(sut):
    """Accessing the singleton again must not wipe queued job IDs.

    Regression: `__init__` used to run on every access and reset `_pending_ids`,
    so a notify enqueue was lost as soon as any request resolved the matcher.
    """
    sut.add_pending_ids([10, 20])

    assert WatcherMatcher() is sut
    assert WatcherMatcher()._pending_ids == {10, 20}


def test_singleton_repeated_access_preserves_running_state(sut):
    """Accessing the singleton again must not stop the background thread."""
    sut._running = True
    sut._thread = MagicMock()

    second = WatcherMatcher()

    assert second is sut
    assert second._running is True
    assert second._thread is sut._thread
    assert second._lock is sut._lock
