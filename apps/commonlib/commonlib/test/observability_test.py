import json
import os

import pytest

from commonlib import observability
from commonlib.observability import configure_logging, get_app_name, get_logger, job_log_context, log_file_path
from commonlib.test.observability_fixtures import APP_NAME_ENV, LEGACY_APP_NAME_ENV, _events, _read, fake_app, log_dir  # noqa: F401 - the fixtures register by being imported here


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

    @pytest.mark.parametrize("env, expected", [(None, True), ("LOG_COLOR", False), ("AI_ENRICH_LOG_COLOR", False)])
    def test_color_enabled(self, log_dir, monkeypatch, env, expected):
        if env:
            monkeypatch.setenv(env, "False")
        assert observability.color_enabled() is expected

    @pytest.mark.parametrize("env, value, expected", [
        (None, None, 20),
        ("LOG_LEVEL", "30", "30"),
        ("AI_ENRICH_LOG_LEVEL", "40", "40"),
    ])
    def test_log_level(self, log_dir, monkeypatch, env, value, expected):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        monkeypatch.delenv("AI_ENRICH_LOG_LEVEL", raising=False)
        if env:
            monkeypatch.setenv(env, value)
        assert observability._env("LOG_LEVEL", "AI_ENRICH_LOG_LEVEL", 20) == expected


class TestAppNameResolution:
    def test_explicit_app_name_wins(self, log_dir):
        assert configure_logging("scrapper") == "scrapper"
        assert get_app_name() == "scrapper"

    def test_default_app_name_without_configuration(self, log_dir):
        assert configure_logging() == "app"

    @pytest.mark.parametrize("env, value", [(APP_NAME_ENV, "fromenv"), (LEGACY_APP_NAME_ENV, "legacy")])
    def test_env_app_name_is_read(self, log_dir, monkeypatch, env, value):
        monkeypatch.setenv(env, value)
        observability._app_name = None
        assert configure_logging() == value

    def test_late_configure_overrides_import_time_default(self, log_dir):
        """A shared module importing first must not win over the entrypoint."""
        assert configure_logging() == "app"
        assert configure_logging("cron") == "cron"
        get_logger("cron.scheduler").info("cron.tick", tick=1)
        assert json.loads(_read(log_file_path("cron")))["logger"] == "cron"

    def test_file_path_follows_app_name(self, log_dir):
        configure_logging("first")
        assert log_file_path() == os.path.join(str(log_dir), "first.jsonl")
        configure_logging("second")
        assert log_file_path() == os.path.join(str(log_dir), "second.jsonl")
        configure_logging("current")
        assert log_file_path("other") == os.path.join(str(log_dir), "other.jsonl")


class TestJsonlRecords:
    def test_log_writes_expected_record(self, log_dir):
        configure_logging("test_jsonl")
        get_logger("test_jsonl.case").info("test.event", key="value", num=42)
        entry = json.loads(_read(log_file_path("test_jsonl")))
        assert (entry["event"], entry["key"], entry["num"], entry["level"], entry["logger"], entry["module"]) == ("test.event", "value", 42, "info", "test_jsonl", "test_jsonl.case")
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


class TestStampCallerModule:
    def test_shared_helper_frame_is_skipped(self, fake_app):
        """The app frame wins over the shared helper the record was logged through."""
        result = fake_app.emit({"module": "commonlib.ai_helpers", "event": "jobs.skipped"})
        assert result["module"] == "fake_app"

    def test_bound_name_is_kept_without_an_app_frame(self, log_dir):
        """This test module is skipped like a helper, so the logger's own name survives."""
        configure_logging("fallback")
        get_logger("fallback.case").info("test.event")
        assert _events(log_file_path("fallback"))[0]["module"] == "fallback.case"

    def test_shared_helper_name_is_kept_without_an_app_frame(self, log_dir):
        """A helper called from a test still reports itself, not the test runner."""
        configure_logging("helper_case")
        get_logger("commonlib.stopWatch").info("job.result", duration=1.0)
        assert _events(log_file_path("helper_case"))[0]["module"] == "commonlib.stopWatch"

    def test_entry_script_does_not_win(self, fake_app):
        """`__main__` above an app frame must not become the module."""
        assert observability.STACK_STOP_MODULES == frozenset({"__main__"})
        assert fake_app.emit({"module": "commonlib.ai_helpers"})["module"] != "__main__"


class TestJobLogContext:
    def test_binds_job_id_only_inside_the_block(self, log_dir):
        configure_logging("ctx_bind")
        logger = get_logger("ctx_bind.case")
        with job_log_context(582714):
            logger.info("job.result", duration=1.0)
        logger.info("jobs.skipped", wait_seconds=10)
        records = _events(log_file_path("ctx_bind"))
        assert records[0]["job_id"] == 582714
        assert "job_id" not in records[1]

    def test_explicit_job_id_wins(self, log_dir):
        configure_logging("ctx_explicit")
        logger = get_logger("ctx_explicit.case")
        with job_log_context(582714):
            logger.info("job.retry", job_id=42)
        assert _events(log_file_path("ctx_explicit"))[0]["job_id"] == 42

    def test_none_job_id_does_not_bind(self, log_dir):
        configure_logging("ctx_none")
        logger = get_logger("ctx_none.case")
        with job_log_context(None):
            logger.info("job.not_found")
        assert "job_id" not in _events(log_file_path("ctx_none"))[0]

    def test_job_id_is_unbound_after_an_error(self, log_dir):
        configure_logging("ctx_error")
        logger = get_logger("ctx_error.case")
        with pytest.raises(ValueError):
            with job_log_context(7):
                raise ValueError("boom")
        logger.info("job.critical_error")
        assert "job_id" not in _events(log_file_path("ctx_error"))[0]

    def test_nested_blocks_inherit_the_inner_id(self, log_dir):
        configure_logging("ctx_nested")
        logger = get_logger("ctx_nested.case")
        with job_log_context(1):
            with job_log_context(2):
                logger.info("job.result")
        assert _events(log_file_path("ctx_nested"))[0]["job_id"] == 2
