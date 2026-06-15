from unittest.mock import MagicMock, ANY
from datetime import datetime, timezone
import pytest
from cron.scheduler import Scheduler, CronJob, _parse_cadency


def test_parse_cadency_seconds():
    assert _parse_cadency("30s") == 30

def test_parse_cadency_minutes():
    assert _parse_cadency("5m") == 300

def test_parse_cadency_hours():
    assert _parse_cadency("2h") == 7200

def test_parse_cadency_days():
    assert _parse_cadency("1d") == 86400

def test_parse_cadency_default():
    assert _parse_cadency("invalid") == 3600

def test_parse_cadency_strips_whitespace():
    assert _parse_cadency(" 10m ") == 600


class _MockJob(CronJob):
    def __init__(self, name="test_job", cadency="1h"):
        self.name = name
        self.cadency = cadency
        self.run_count = 0
        self.should_fail = False

    def run(self, cron_state):
        self.run_count += 1
        if self.should_fail:
            raise RuntimeError("job failed")


def test_scheduler_first_tick_runs_all_jobs():
    cron_state = MagicMock()
    cron_state.get_state.return_value = None
    job = _MockJob()
    sut = Scheduler(cron_state, [job])

    sut.tick()

    assert job.run_count == 1
    cron_state.update_state.assert_called_once()

def test_scheduler_second_tick_skips_if_cadency_not_met():
    now = datetime.now(timezone.utc)
    cron_state = MagicMock()
    cron_state.get_state.return_value = {"last_run_at": now, "status": "ok"}
    job = _MockJob(cadency="1h")
    sut = Scheduler(cron_state, [job])

    sut.tick()
    sut.tick()

    assert job.run_count == 1

def test_scheduler_re_runs_errored_jobs():
    now = datetime.now(timezone.utc)
    cron_state = MagicMock()
    cron_state.get_state.return_value = {"last_run_at": now, "status": "error"}
    job = _MockJob(cadency="1h")
    sut = Scheduler(cron_state, [job])

    sut.tick()
    assert job.run_count == 1
    sut.tick()
    assert job.run_count == 2

def test_scheduler_parses_string_last_run_at():
    cron_state = MagicMock()
    cron_state.get_state.return_value = {
        "last_run_at": "2020-01-01T00:00:00",
        "status": "ok",
    }
    job = _MockJob(cadency="1s")
    sut = Scheduler(cron_state, [job])

    sut.tick()
    sut.tick()

    assert job.run_count == 2

def test_scheduler_job_failure_updates_error_state():
    cron_state = MagicMock()
    cron_state.get_state.return_value = None
    job = _MockJob(name="fail_job")
    job.should_fail = True
    sut = Scheduler(cron_state, [job])

    sut.tick()

    assert job.run_count == 1
    cron_state.update_state.assert_called_once_with("fail_job", {
        "last_run_at": ANY,
        "status": "error",
        "error": "job failed",
    })

def test_cron_job_base_run_raises():
    with pytest.raises(NotImplementedError):
        CronJob().run(None)
