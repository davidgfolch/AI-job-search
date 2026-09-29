import json
import os

import pytest

from commonlib import observability
from commonlib.observability import configure_logging, get_app_name, get_logger, log_file_path

APP_NAME_ENV = "LOG_APP_NAME"
LEGACY_APP_NAME_ENV = "AI_ENRICH_LOG_APP_NAME"


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    """Redirect the JSONL output to a temp dir and reset the app name."""
    target = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(target))
    monkeypatch.delenv(APP_NAME_ENV, raising=False)
    monkeypatch.delenv(LEGACY_APP_NAME_ENV, raising=False)
    observability._app_name = None
    yield target
    observability._app_name = None


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.readline().strip()


def _events(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class TestConfiguration:
    def test_configure_logging_is_idempotent(self, log_dir):
        assert configure_logging("test") == "test"
        assert configure_logging("test") == "test"
        assert get_app_name() == "test"

    def test_get_logger_returns_bound_logger(self, log_dir):
        logger = get_logger("test")
        for level in ("info", "error", "debug", "warning", "exception"):
            assert hasattr(logger, level)

    def test_get_logger_binds_module_name(self, log_dir):
        assert get_logger("my.module")._context["module"] == "my.module"

    def test_structlog_configured(self, log_dir):
        import structlog

        configure_logging("test")
        processors = structlog.get_config()["processors"]
        assert any("add_log_level" in str(p) for p in processors)
        assert any(isinstance(p, structlog.processors.ExceptionRenderer) for p in processors)

    def test_color_enabled_by_default(self, log_dir):
        assert observability.color_enabled() is True

    def test_color_disabled_by_env(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_COLOR", "False")
        assert observability.color_enabled() is False

    def test_color_enabled_by_legacy_env(self, log_dir, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_LOG_COLOR", "False")
        assert observability.color_enabled() is False

    def test_log_level_defaults_to_info(self, log_dir, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("AI_ENRICH_LOG_LEVEL", raising=False)
        assert observability._env("LOG_LEVEL", "AI_ENRICH_LOG_LEVEL", 20) == 20

    def test_log_level_read_from_env(self, log_dir, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "30")
        assert observability._env("LOG_LEVEL", "AI_ENRICH_LOG_LEVEL", 20) == "30"

    def test_log_level_legacy_alias(self, log_dir, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_LOG_LEVEL", "40")
        assert observability._env("LOG_LEVEL", "AI_ENRICH_LOG_LEVEL", 20) == "40"


class TestAppNameResolution:
    def test_explicit_app_name_wins(self, log_dir):
        assert configure_logging("scrapper") == "scrapper"
        assert get_app_name() == "scrapper"

    def test_default_app_name_without_configuration(self, log_dir):
        assert configure_logging() == "app"

    def test_get_logger_before_configure_uses_env_default(self, log_dir, monkeypatch):
        monkeypatch.setenv(APP_NAME_ENV, "fromenv")
        observability._app_name = None
        assert configure_logging() == "fromenv"

    def test_legacy_env_alias_still_read(self, log_dir, monkeypatch):
        monkeypatch.setenv(LEGACY_APP_NAME_ENV, "legacy")
        observability._app_name = None
        assert configure_logging() == "legacy"

    def test_late_configure_overrides_import_time_default(self, log_dir):
        """A shared module importing first must not win over the entrypoint."""
        assert configure_logging() == "app"
        assert configure_logging("cron") == "cron"
        get_logger("cron.scheduler").info("cron.tick", tick=1)
        entry = json.loads(_read(log_file_path("cron")))
        assert entry["logger"] == "cron"

    def test_file_path_follows_current_app_name(self, log_dir):
        configure_logging("first")
        assert log_file_path() == os.path.join(str(log_dir), "first.jsonl")
        configure_logging("second")
        assert log_file_path() == os.path.join(str(log_dir), "second.jsonl")

    def test_file_path_accepts_explicit_app_name(self, log_dir):
        configure_logging("current")
        assert log_file_path("other") == os.path.join(str(log_dir), "other.jsonl")


class TestJsonlRecords:
    def test_log_writes_expected_record(self, log_dir):
        configure_logging("test_jsonl")
        get_logger("test_jsonl.case").info("test.event", key="value", num=42)
        entry = json.loads(_read(log_file_path("test_jsonl")))
        assert entry["event"] == "test.event"
        assert entry["key"] == "value"
        assert entry["num"] == 42
        assert entry["level"] == "info"
        assert entry["logger"] == "test_jsonl"
        assert entry["module"] == "test_jsonl.case"
        assert "timestamp" in entry

    def test_creates_missing_log_dir(self, log_dir):
        assert not log_dir.exists()
        configure_logging("mkdir_test")
        get_logger("mkdir_test.case").info("test.event")
        assert os.path.exists(log_file_path("mkdir_test"))

    def test_exception_records_traceback(self, log_dir):
        configure_logging("exc_test")
        logger = get_logger("exc_test.case")
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("test.failed")
        entry = json.loads(_read(log_file_path("exc_test")))
        assert entry["level"] == "error"
        assert "ValueError" in entry["exception"]

    def test_unserializable_values_do_not_raise(self, log_dir):
        configure_logging("obj_test")
        get_logger("obj_test.case").info("test.event", payload=object())
        assert json.loads(_read(log_file_path("obj_test")))["event"] == "test.event"
