import json
import os
from unittest.mock import patch

import pytest

from commonlib import log_writer
from commonlib.log_writer import append_jsonl, file_backup_count, file_max_bytes, get_log_dir, make_jsonl_writer, resolve_read_path, rotate_if_needed


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    monkeypatch.delenv("AI_ENRICH_LOG_DIR", raising=False)
    yield tmp_path


def _seed(path, size: int) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("x" * size)


def _events(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class TestEnvironmentResolution:
    def test_default_log_dir(self, log_dir, monkeypatch):
        monkeypatch.delenv("LOG_DIR", raising=False)
        assert get_log_dir() == log_writer.DEFAULT_LOG_DIR

    def test_legacy_log_dir_used_as_fallback(self, log_dir, monkeypatch):
        monkeypatch.delenv("LOG_DIR", raising=False)
        monkeypatch.setenv("AI_ENRICH_LOG_DIR", "/legacy/dir")
        assert get_log_dir() == "/legacy/dir"

    def test_primary_log_dir_wins_over_legacy(self, log_dir, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_LOG_DIR", "/legacy")
        assert get_log_dir() == str(log_dir)

    def test_legacy_size_and_count_aliases(self, log_dir, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_LOG_FILE_MAX_BYTES", "4242")
        monkeypatch.setenv("AI_ENRICH_LOG_FILE_BACKUP_COUNT", "3")
        assert file_max_bytes() == 4242
        assert file_backup_count() == 3

    def test_empty_value_falls_back_to_default(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_DIR", "")
        monkeypatch.setenv("AI_ENRICH_LOG_DIR", "")
        assert get_log_dir() == log_writer.DEFAULT_LOG_DIR


class TestRotation:
    def test_rotates_once_over_max_bytes(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "100")
        path = str(log_dir / "rot.jsonl")
        _seed(path, 101)
        rotate_if_needed(path)
        assert os.path.exists(f"{path}.1")
        assert not os.path.exists(path)

    def test_keeps_under_max_bytes_untouched(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "100")
        path = str(log_dir / "rot.jsonl")
        _seed(path, 50)
        rotate_if_needed(path)
        assert not os.path.exists(f"{path}.1")
        assert os.path.exists(path)

    def test_missing_file_does_not_rotate(self, log_dir):
        path = str(log_dir / "absent.jsonl")
        with patch("os.replace", side_effect=AssertionError("should not rotate")):
            rotate_if_needed(path)

    def test_backup_count_limits_rotations(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "10")
        monkeypatch.setenv("LOG_FILE_BACKUP_COUNT", "2")
        path = str(log_dir / "rot.jsonl")
        for _ in range(3):
            _seed(path, 20)
            rotate_if_needed(path)
        assert os.path.exists(f"{path}.1")
        assert os.path.exists(f"{path}.2")
        assert not os.path.exists(f"{path}.3")

    def test_rotation_survives_oserror(self, log_dir):
        path = str(log_dir / "rot.jsonl")
        _seed(path, 10**9)
        with patch("os.replace", side_effect=OSError("permission denied")):
            rotate_if_needed(path)
        assert os.path.exists(path)

    def test_shift_survives_oserror(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "10")
        monkeypatch.setenv("LOG_FILE_BACKUP_COUNT", "5")
        path = str(log_dir / "rot.jsonl")
        _seed(path, 20)
        _seed(f"{path}.1", 5)
        with patch("os.replace", side_effect=OSError("permission denied")):
            rotate_if_needed(path)


class TestAppend:
    def test_appends_jsonl_records(self, log_dir):
        path = str(log_dir / "a.jsonl")
        append_jsonl(path, {"event": "one"})
        append_jsonl(path, {"event": "two"})
        assert _events(path) == [{"event": "one"}, {"event": "two"}]

    def test_creates_missing_directory(self, log_dir):
        path = str(log_dir / "nested" / "a.jsonl")
        append_jsonl(path, {"event": "one"})
        assert os.path.exists(path)

    def test_handles_bare_filename(self, log_dir, monkeypatch):
        monkeypatch.chdir(log_dir)
        append_jsonl("bare.jsonl", {"event": "one"})
        assert os.path.exists("bare.jsonl")

    def test_unserializable_values_do_not_raise(self, log_dir):
        path = str(log_dir / "a.jsonl")
        append_jsonl(path, {"event": "one", "payload": object()})
        assert _events(path)[0]["event"] == "one"

    def test_write_oserror_is_swallowed(self, log_dir):
        with patch("builtins.open", side_effect=OSError("disk full")):
            append_jsonl(str(log_dir / "a.jsonl"), {"event": "one"})

    def test_makedirs_oserror_is_swallowed(self, log_dir):
        with patch("os.makedirs", side_effect=OSError("read only fs")):
            append_jsonl(str(log_dir / "a.jsonl"), {"event": "one"})


class TestWriterFactory:
    def test_stamps_and_appends(self, log_dir):
        path = str(log_dir / "w.jsonl")
        writer = make_jsonl_writer(lambda: path, lambda record: record.update(logger="svc"))
        result = writer(None, "info", {"event": "test.event", "level": "info"})
        assert result["logger"] == "svc"
        assert _events(path) == [{"event": "test.event", "level": "info", "logger": "svc"}]

    def test_resolves_path_per_record(self, log_dir):
        paths = [str(log_dir / "a.jsonl"), str(log_dir / "b.jsonl")]
        writer = make_jsonl_writer(lambda: paths.pop(0), lambda record: None)
        writer(None, "info", {"event": "first"})
        writer(None, "info", {"event": "second"})
        assert _events(str(log_dir / "a.jsonl")) == [{"event": "first"}]
        assert _events(str(log_dir / "b.jsonl")) == [{"event": "second"}]

    def test_rotates_before_writing(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_FILE_MAX_BYTES", "50")
        path = str(log_dir / "w.jsonl")
        _seed(path, 60)
        writer = make_jsonl_writer(lambda: path, lambda record: None)
        writer(None, "info", {"event": "after_rotate"})
        assert _events(path) == [{"event": "after_rotate"}]
        assert os.path.exists(f"{path}.1")

    def test_private_keys_are_dropped_from_the_file(self, log_dir):
        path = str(log_dir / "w.jsonl")
        writer = make_jsonl_writer(lambda: path, lambda record: None)
        result = writer(None, "info", {"event": "scraper.started", "_console": "RUNNING Linkedin"})
        assert _events(path) == [{"event": "scraper.started"}]
        assert result["_console"] == "RUNNING Linkedin"


def test_resolve_read_path_prefers_per_app_name(log_dir):
    app = log_dir / "cron.jsonl"
    legacy = log_dir / log_writer.LEGACY_LOG_FILE_NAME
    _seed(str(app), 10)
    _seed(str(legacy), 10)
    assert resolve_read_path(str(app)) == str(app)


def test_resolve_read_path_falls_back_to_legacy(log_dir):
    app = log_dir / "cron.jsonl"
    legacy = log_dir / log_writer.LEGACY_LOG_FILE_NAME
    _seed(str(legacy), 10)
    assert resolve_read_path(str(app)) == str(legacy)


def test_resolve_read_path_returns_none_when_absent(log_dir):
    assert resolve_read_path(str(log_dir / "cron.jsonl")) is None
