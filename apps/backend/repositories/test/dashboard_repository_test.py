import json
import os
import tempfile
from unittest.mock import patch

from repositories.dashboard_repository import DashboardRepository


def _write_log(path, entries):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def test_read_recent_errors(tmp_path):
    log_file = tmp_path / "app.jsonl"
    _write_log(str(log_file), [
        {"timestamp": "2026-09-03T10:00:01", "event": "job.result", "level": "info", "duration": 1.0},
        {"timestamp": "2026-09-03T10:00:02", "event": "ollama.ping_failed", "level": "error", "error": "timeout"},
        {"timestamp": "2026-09-03T10:00:03", "event": "job.failed", "level": "error", "error": "boom", "job_id": 5},
        {"timestamp": "2026-09-03T10:00:04", "event": "job.retry", "level": "warning", "job_id": 6},
    ])
    repo = DashboardRepository()
    with patch("repositories.dashboard_repository.LOG_SOURCES", {"aienrich": str(log_file)}):
        errors = repo.read_recent_errors("aienrich")
    assert len(errors) == 3
    assert errors[0]["event"] == "job.retry"
    assert errors[1]["event"] == "job.failed"
    assert "boom" in errors[1]["message"]
    assert "job=5" in errors[1]["message"]


def test_read_recent_errors_missing_file():
    repo = DashboardRepository()
    assert repo.read_recent_errors("nonexistent") == []


def test_read_recent_errors_invalid_module():
    repo = DashboardRepository()
    assert repo.read_recent_errors("unknown") == []


def test_read_last_activity(tmp_path):
    log_file = tmp_path / "app.jsonl"
    _write_log(str(log_file), [
        {"timestamp": "2026-09-03T10:00:01", "event": "job.result", "level": "info"},
        {"timestamp": "2026-09-03T10:00:05", "event": "job.result", "level": "info"},
    ])
    repo = DashboardRepository()
    with patch("repositories.dashboard_repository.LOG_SOURCES", {"aienrich": str(log_file)}):
        result = repo.read_last_activity("aienrich")
    assert result == "2026-09-03T10:00:05"


def test_check_ollama_errors(tmp_path):
    log_file = tmp_path / "app.jsonl"
    _write_log(str(log_file), [
        {"timestamp": "2026-09-03T10:00:01", "event": "ollama.ping_failed", "level": "error", "error": "conn refused"},
        {"timestamp": "2026-09-03T10:00:02", "event": "job.result", "level": "info"},
    ])
    repo = DashboardRepository()
    with patch("repositories.dashboard_repository.LOG_SOURCES", {"aienrich": str(log_file)}):
        errors = repo.check_ollama_errors()
    assert len(errors) == 1
    assert errors[0]["event"] == "ollama.ping_failed"
    assert errors[0]["module"] == "aienrich"


def test_check_ollama_errors_no_matches(tmp_path):
    log_file = tmp_path / "app.jsonl"
    _write_log(str(log_file), [
        {"timestamp": "2026-09-03T10:00:01", "event": "job.result", "level": "info"},
    ])
    repo = DashboardRepository()
    with patch("repositories.dashboard_repository.LOG_SOURCES", {"aienrich": str(log_file)}):
        errors = repo.check_ollama_errors()
    assert errors == []
