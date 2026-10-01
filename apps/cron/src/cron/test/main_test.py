import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from commonlib.observability import get_app_name, log_file_path
from cron import main


class _StopLoop(Exception):
    pass


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    return tmp_path


def _events():
    path = Path(log_file_path())
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _raw_log():
    path = Path(log_file_path())
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _run_one_tick():
    with patch("cron.main.get_mongo_provider") as mock_provider, patch("cron.main.Scheduler") as mock_scheduler_cls, patch("cron.main.time.sleep", side_effect=_StopLoop):
        mock_scheduler_cls.return_value = MagicMock()
        with pytest.raises(_StopLoop):
            main.run()
    return mock_provider, mock_scheduler_cls


def test_run_names_the_log_file_after_the_app(log_dir):
    _run_one_tick()
    assert get_app_name() == "cron"
    assert log_file_path().endswith("cron.jsonl")


def test_run_configures_logging_before_connecting_to_mongo(log_dir):
    with patch("cron.main.configure_logging") as mock_configure, patch("cron.main.get_mongo_provider") as mock_provider, patch("cron.main.Scheduler"), patch("cron.main.time.sleep", side_effect=_StopLoop):
        order = MagicMock()
        order.attach_mock(mock_configure, "configure")
        order.attach_mock(mock_provider, "provider")
        with pytest.raises(_StopLoop):
            main.run()
    assert [name for name, _, _ in order.mock_calls][:2] == ["configure", "provider"]
    assert order.configure.call_args.args == ("cron",)


def test_run_emits_lifecycle_events_in_order(log_dir):
    _run_one_tick()
    assert [e["event"] for e in _events()] == ["cron.started", "cron.jobs_registered", "cron.tick"]


def test_run_records_job_count_and_interval(log_dir):
    _run_one_tick()
    registered = _events()[1]
    assert registered["jobs"] == 1
    assert registered["check_interval_seconds"] == 60
    assert registered["level"] == "info"


def test_run_ticks_the_scheduler_once_per_iteration(log_dir):
    _, mock_scheduler_cls = _run_one_tick()
    assert mock_scheduler_cls.return_value.tick.call_count == 1


def test_run_never_logs_mongo_credentials(log_dir):
    _run_one_tick()
    raw = _raw_log()
    assert raw
    assert "mongodb://" not in raw
    assert "rootPass" not in raw
