import pytest
from unittest.mock import MagicMock, patch
from services.watcher_matcher import WatcherMatcher


@pytest.fixture(autouse=True)
def reset_singleton():
    WatcherMatcher.reset_for_testing()
    yield


@pytest.fixture
def mock_repos():
    """Mock both WatcherRepository (reads) and WatcherMatchRepository (writes)."""
    with patch(
        "services.watcher_matcher.WatcherRepository"
    ) as mock_repo_cls, patch(
        "services.watcher_matcher.WatcherMatchRepository"
    ) as mock_match_repo_cls:
        mock_repo = MagicMock()
        mock_match_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_match_repo_cls.return_value = mock_match_repo
        yield mock_repo, mock_match_repo


def test_full_flow_create_job_then_stats(mock_repos):
    """Full flow: pending job IDs are matched against filter configs."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    mock_repo.get_watched_configs.return_value = [
        (1, '{"search": "python"}'),
        (2, '{"boolean_filters": {"applied": true}}'),
    ]

    mock_repo.get_existing_job_ids.return_value = {10, 20}

    def match_side_effect(config_id, where_part, job_ids):
        if config_id == 1:
            return [10]
        if config_id == 2:
            return [20]
        return []

    mock_repo.match_jobs_against_config.side_effect = match_side_effect

    service.add_pending_ids([10, 20, 30])
    service._process_pending()

    mock_match_repo.insert_match.assert_any_call(1, 10)
    mock_match_repo.insert_match.assert_any_call(2, 20)
    assert mock_match_repo.insert_match.call_count == 2


def test_full_flow_deleted_job_produces_tombstone(mock_repos):
    """Deleted job: active matches removed, tombstone inserted."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    mock_repo.get_watched_configs.return_value = [
        (1, '{"search": "python"}'),
    ]

    mock_repo.get_existing_job_ids.return_value = set()
    mock_repo.get_active_matches_for_jobs.return_value = [(1, 99)]

    service.add_pending_ids([99])
    service._process_pending()

    mock_match_repo.delete_active_matches_for_jobs.assert_called_once_with([99])
    mock_match_repo.insert_tombstone.assert_called_once_with(1, 99)


def test_process_pending_no_configs(mock_repos):
    """If no watched configs, process_pending should be a no-op."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    mock_repo.get_watched_configs.return_value = []

    service.add_pending_ids([1, 2, 3])
    service._process_pending()

    mock_match_repo.insert_match.assert_not_called()
    mock_match_repo.insert_tombstone.assert_not_called()


def test_process_pending_empty_pending(mock_repos):
    """If no pending IDs, process_pending should be a no-op."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    service._process_pending()

    mock_repo.get_watched_configs.assert_not_called()
    mock_match_repo.insert_match.assert_not_called()


def test_handle_deleted_jobs_inserts_tombstones(mock_repos):
    """_handle_deleted_jobs inserts tombstones for each active match of deleted jobs."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    mock_repo.get_active_matches_for_jobs.return_value = [(1, 5), (2, 5)]

    service._handle_deleted_jobs({5})

    mock_match_repo.delete_active_matches_for_jobs.assert_called_once_with([5])
    mock_match_repo.insert_tombstone.assert_any_call(1, 5)
    mock_match_repo.insert_tombstone.assert_any_call(2, 5)
    assert mock_match_repo.insert_tombstone.call_count == 2


def test_handle_deleted_jobs_empty(mock_repos):
    """_handle_deleted_jobs with empty set is a no-op."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    service._handle_deleted_jobs(set())

    mock_repo.get_active_matches_for_jobs.assert_not_called()
    mock_match_repo.insert_tombstone.assert_not_called()


def test_match_existing_jobs_inserts_matches(mock_repos):
    """_match_existing_jobs runs filter SQL against existing jobs and inserts matches."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    mock_repo.match_jobs_against_config.return_value = [10, 20]

    service._match_existing_jobs(
        {10, 20, 30}, [(1, '{"search": "python"}')]
    )

    mock_repo.match_jobs_against_config.assert_called_once()
    call_args = mock_repo.match_jobs_against_config.call_args
    assert call_args[0][0] == 1
    assert isinstance(call_args[0][1], str) and len(call_args[0][1]) > 0
    assert call_args[0][2] == [10, 20, 30]
    mock_match_repo.insert_match.assert_any_call(1, 10)
    mock_match_repo.insert_match.assert_any_call(1, 20)


def test_match_existing_jobs_empty(mock_repos):
    """_match_existing_jobs with empty set is a no-op."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    service._match_existing_jobs(set(), [(1, "{}")])

    mock_repo.match_jobs_against_config.assert_not_called()
    mock_match_repo.insert_match.assert_not_called()


def test_match_config_omits_sql_from_info_record(mock_repos):
    """The info record carries ids and counts only; the SQL lives in the debug record."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()
    mock_repo.match_jobs_against_config.return_value = [10]

    with patch("services.watcher_matcher.logger") as mock_logger:
        service._match_existing_jobs({10}, [(1, '{"search": "python"}')])

    info_calls = [c for c in mock_logger.info.call_args_list if c.args[0] == "watcher.match_config"]
    assert len(info_calls) == 1
    assert info_calls[0].kwargs == {"config_id": 1, "matched": 1, "matched_ids": [10]}

    debug_calls = [c for c in mock_logger.debug.call_args_list if c.args[0] == "watcher.match_config_query"]
    assert len(debug_calls) == 1
    assert debug_calls[0].kwargs["config_id"] == 1
    assert debug_calls[0].kwargs["filters"] == {"search": "python"}
    assert "where" in debug_calls[0].kwargs


def test_match_config_not_logged_without_matches(mock_repos):
    """A config that matched nothing produces no info record, only the debug one."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()
    mock_repo.match_jobs_against_config.return_value = []

    with patch("services.watcher_matcher.logger") as mock_logger:
        service._match_existing_jobs({10}, [(1, '{"search": "python"}')])

    info_events = [c.args[0] for c in mock_logger.info.call_args_list]
    assert "watcher.match_config" not in info_events
    debug_events = [c.args[0] for c in mock_logger.debug.call_args_list]
    assert "watcher.match_config_query" in debug_events


def test_process_pending_logs_count_without_ids(mock_repos):
    """The tick record carries the count; the id list is debug-only."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()
    mock_repo.get_watched_configs.return_value = []
    service.add_pending_ids([10, 20])

    with patch("services.watcher_matcher.logger") as mock_logger:
        service._process_pending()

    info_calls = [c for c in mock_logger.info.call_args_list if c.args[0] == "watcher.process_pending"]
    assert [c.kwargs for c in info_calls] == [{"count": 2}]
    debug_calls = [c for c in mock_logger.debug.call_args_list if c.args[0] == "watcher.process_pending_ids"]
    assert [c.kwargs for c in debug_calls] == [{"pending_ids": [10, 20]}]


def test_parse_filters_valid_json(mock_repos):
    """_parse_filters parses valid JSON string into a dict."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    result = service._parse_filters('{"search": "python"}')
    assert result == {"search": "python"}


def test_parse_filters_invalid_json_returns_empty(mock_repos):
    """_parse_filters returns {} for invalid JSON."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    result = service._parse_filters("not-json")
    assert result == {}


def test_parse_filters_none_returns_empty(mock_repos):
    """_parse_filters returns {} for None."""
    mock_repo, mock_match_repo = mock_repos
    service = WatcherMatcher()

    result = service._parse_filters(None)
    assert result == {}


def test_singleton_repeated_access_preserves_pending_ids(mock_repos):
    """Accessing the singleton again must not wipe queued job IDs.

    Regression: `__init__` used to run on every access and reset `_pending_ids`,
    so a notify enqueue was lost as soon as any request resolved the matcher.
    """
    first = WatcherMatcher()
    first.add_pending_ids([10, 20])

    second = WatcherMatcher()

    assert second is first
    assert second._pending_ids == {10, 20}


def test_singleton_repeated_access_preserves_running_state(mock_repos):
    """Accessing the singleton again must not stop the background thread."""
    first = WatcherMatcher()
    first._running = True
    first._thread = MagicMock()

    second = WatcherMatcher()

    assert second is first
    assert second._running is True
    assert second._thread is first._thread
    assert second._lock is first._lock
