import pytest
from unittest.mock import patch

from ..idle_scheduler import LearningPathScheduler, should_run_learning_paths


@pytest.mark.parametrize("failures, expected_open, expected_ready", [
    pytest.param(1, False, True, id="below_threshold"),
    pytest.param(2, True, False, id="reaches_threshold"),
], ids=lambda value: None)
def test_scheduler_circuit_breaker(failures, expected_open, expected_ready):
    scheduler = LearningPathScheduler(max_failures=2)
    opened = False
    for _ in range(failures):
        opened = scheduler.note_failure()
    assert opened is expected_open
    assert scheduler.ready() is expected_ready


def test_scheduler_success_resets_failure_count():
    scheduler = LearningPathScheduler(max_failures=2)
    scheduler.note_failure()
    scheduler.note_success()
    assert scheduler.note_failure() is False
    assert scheduler.note_failure() is True


def test_scheduler_tracks_deferred_transition():
    scheduler = LearningPathScheduler(max_failures=3)
    assert scheduler.deferred is False
    scheduler.note_deferred("model_busy")
    assert scheduler.deferred is True


def test_scheduler_started_clears_deferred_state():
    scheduler = LearningPathScheduler(max_failures=3)
    scheduler.note_deferred("model_busy")
    scheduler.note_started()
    assert scheduler.deferred is False


def test_scheduler_stopped_clears_deferred_state():
    scheduler = LearningPathScheduler(max_failures=3)
    scheduler.note_deferred("model_busy")
    scheduler.note_stopped()
    assert scheduler.deferred is False


@patch("aiEnrichSkill.services.idle_scheduler.busy_seconds", return_value=12.6)
@patch("aiEnrichSkill.services.idle_scheduler.logger")
def test_scheduler_logs_deferred_once_per_streak(mock_logger, _busy):
    scheduler = LearningPathScheduler(max_failures=3)
    scheduler.note_deferred("model_busy")
    scheduler.note_deferred("model_busy")
    scheduler.note_deferred("model_busy")
    mock_logger.info.assert_called_once_with("skill.learning_path.deferred", reason="model_busy", model_busy_seconds=12)


@patch("aiEnrichSkill.services.idle_scheduler.logger")
def test_scheduler_logs_started_once_per_streak(mock_logger):
    scheduler = LearningPathScheduler(max_failures=3)
    scheduler.note_deferred("model_busy")
    scheduler.note_started()
    scheduler.note_started()
    started = [c for c in mock_logger.info.call_args_list if c.args and c.args[0] == "skill.learning_path.started"]
    assert len(started) == 1


@patch("aiEnrichSkill.services.idle_scheduler.get_learning_paths_enabled", return_value=False)
def test_should_not_run_when_feature_disabled(_enabled):
    assert should_run_learning_paths(LearningPathScheduler()) is False


@patch("aiEnrichSkill.services.idle_scheduler.get_learning_paths_enabled", return_value=True)
def test_should_run_when_enabled_and_breaker_closed(_enabled):
    assert should_run_learning_paths(LearningPathScheduler()) is True


@patch("aiEnrichSkill.services.idle_scheduler.get_learning_paths_enabled", return_value=True)
def test_should_not_run_when_breaker_open(_enabled):
    scheduler = LearningPathScheduler(max_failures=1)
    scheduler.note_failure()
    assert should_run_learning_paths(scheduler) is False


@patch("aiEnrichSkill.services.idle_scheduler.time.monotonic")
@pytest.mark.parametrize("elapsed, expected_ready", [
    pytest.param(0, False, id="before_window"),
    pytest.param(899, False, id="just_before_window"),
    pytest.param(900, True, id="at_window"),
], ids=lambda value: None)
def test_scheduler_retries_after_cooldown(mock_time, elapsed, expected_ready):
    mock_time.return_value = 1000.0
    scheduler = LearningPathScheduler(max_failures=1, retry_seconds=900)
    scheduler.note_failure()
    mock_time.return_value = 1000.0 + elapsed
    assert scheduler.ready() is expected_ready


@patch("aiEnrichSkill.services.idle_scheduler.logger")
@patch("aiEnrichSkill.services.idle_scheduler.time.monotonic", return_value=1000.0)
def test_scheduler_logs_retry_once_per_open_window(_mock_time, mock_logger):
    scheduler = LearningPathScheduler(max_failures=1, retry_seconds=0)
    scheduler.note_failure()
    assert scheduler.ready() is True
    assert scheduler.ready() is True
    retry = [c for c in mock_logger.info.call_args_list if c.args and c.args[0] == "skill.learning_path.retry"]
    assert len(retry) == 1


@patch("aiEnrichSkill.services.idle_scheduler.time.monotonic")
def test_failed_trial_reopens_breaker_with_fresh_window(mock_time):
    mock_time.return_value = 1000.0
    scheduler = LearningPathScheduler(max_failures=1, retry_seconds=900)
    scheduler.note_failure()
    mock_time.return_value = 1900.0
    assert scheduler.ready() is True
    mock_time.return_value = 2000.0
    assert scheduler.note_failure() is True
    mock_time.return_value = 2800.0
    assert scheduler.ready() is False
    mock_time.return_value = 2900.0
    assert scheduler.ready() is True


@patch("aiEnrichSkill.services.idle_scheduler.time.monotonic", return_value=1000.0)
def test_success_after_retry_resets_failure_count(_mock_time):
    scheduler = LearningPathScheduler(max_failures=2, retry_seconds=0)
    scheduler.note_failure()
    scheduler.note_failure()
    assert scheduler.ready() is True
    scheduler.note_success()
    assert scheduler.note_failure() is False
    assert scheduler.ready() is True
