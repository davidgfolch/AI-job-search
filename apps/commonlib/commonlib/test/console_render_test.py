import json

import pytest

from commonlib import console_render, observability
from commonlib.console_render import CONSOLE_MESSAGE, CONSOLE_RECORD, console_mode
from commonlib.observability import configure_logging, get_logger, log_file_path
from commonlib.terminalColor import green, stripAnsi

LEGACY_ENV = ("AI_ENRICH_LOG_CONSOLE_MODE",)


@pytest.fixture
def console(log_dir, monkeypatch):
    """Redirect the JSONL output, reset the app name and the console mode."""
    for name in ("LOG_CONSOLE_MODE", *LEGACY_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("LOG_COLOR", raising=False)
    observability._app_name = None
    console_render.set_console_mode(None)
    yield log_dir
    observability._app_name = None
    console_render.set_console_mode(None)


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    target = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(target))
    monkeypatch.delenv("AI_ENRICH_LOG_DIR", raising=False)
    return target


def _events(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class TestConsoleModeResolution:
    def test_defaults_to_record(self, console):
        assert console_mode() == CONSOLE_RECORD

    def test_explicit_argument_wins(self, console):
        configure_logging("scrapper", console=CONSOLE_MESSAGE)
        assert console_mode() == CONSOLE_MESSAGE

    def test_env_selects_mode(self, console, monkeypatch):
        monkeypatch.setenv("LOG_CONSOLE_MODE", CONSOLE_MESSAGE)
        assert console_mode() == CONSOLE_MESSAGE

    def test_legacy_env_alias_still_read(self, console, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_LOG_CONSOLE_MODE", CONSOLE_MESSAGE)
        assert console_mode() == CONSOLE_MESSAGE

    def test_late_configure_repoints_mode(self, console):
        """Shared modules log at import time, before the entrypoint selects a mode."""
        configure_logging()
        assert console_mode() == CONSOLE_RECORD
        configure_logging("scrapper", console=CONSOLE_MESSAGE)
        assert console_mode() == CONSOLE_MESSAGE

    def test_get_logger_keeps_the_selected_mode(self, console):
        """`get_logger` re-enters `configure_logging` with no arguments."""
        configure_logging("scrapper", console=CONSOLE_MESSAGE)
        get_logger("scrapper.case")
        assert console_mode() == CONSOLE_MESSAGE


class TestConsoleField:
    def test_console_text_is_printed(self, console, capsys):
        configure_logging("printed", console=CONSOLE_MESSAGE)
        get_logger("printed.case").info("scraper.page_loaded", page=3, console="Starting page 3")
        assert capsys.readouterr().out == "Starting page 3\n"

    def test_console_text_keeps_ansi_by_default(self, console, capsys):
        configure_logging("colored", console=CONSOLE_MESSAGE)
        get_logger("colored.case").info("scraper.started", console=green("RUNNING Linkedin"))
        assert green("RUNNING Linkedin") in capsys.readouterr().out

    def test_console_text_is_stripped_without_color(self, console, capsys, monkeypatch):
        monkeypatch.setenv("LOG_COLOR", "False")
        configure_logging("plain", console=CONSOLE_MESSAGE)
        get_logger("plain.case").info("scraper.started", console=green("RUNNING Linkedin"))
        assert capsys.readouterr().out == "RUNNING Linkedin\n"

    def test_console_text_prints_in_record_mode_too(self, console, capsys):
        configure_logging("both", console=CONSOLE_RECORD)
        get_logger("both.case").info("scraper.started", console="RUNNING Linkedin")
        assert capsys.readouterr().out == "RUNNING Linkedin\n"

    def test_non_string_console_value_is_printed(self, console, capsys):
        configure_logging("coerced", console=CONSOLE_MESSAGE)
        get_logger("coerced.case").info("scraper.started", console=42)
        assert capsys.readouterr().out == "42\n"

    def test_console_field_never_reaches_the_file(self, console, capsys):
        configure_logging("clean", console=CONSOLE_MESSAGE)
        get_logger("clean.case").info("scraper.started", console=green("RUNNING Linkedin"))
        record = _events(log_file_path("clean"))[0]
        assert record["message"] == "RUNNING Linkedin"
        assert "console" not in record
        assert "_console" not in record
        assert "\x1b" not in json.dumps(record)

    def test_existing_message_field_is_kept(self, console, capsys):
        configure_logging("keep", console=CONSOLE_MESSAGE)
        get_logger("keep.case").info("scraper.started", message="raw value", console="human line")
        record = _events(log_file_path("keep"))[0]
        assert record["message"] == "raw value"
        assert capsys.readouterr().out == "human line\n"

    def test_console_text_records_still_keep_fields(self, console, capsys):
        configure_logging("fields", console=CONSOLE_MESSAGE)
        get_logger("fields.case").info("scraper.page_loaded", page=3, total=10, console="page 3 of 10")
        record = _events(log_file_path("fields"))[0]
        assert record["event"] == "scraper.page_loaded"
        assert record["page"] == 3
        assert record["total"] == 10
        assert record["level"] == "info"
        assert record["logger"] == "fields"
        assert record["module"] == "fields.case"


class TestConsoleEnd:
    def test_end_empty_keeps_the_line_open(self, console, capsys):
        """A `print(..., end='')` progress prefix, rebuilt from structured records."""
        configure_logging("progress", console=CONSOLE_MESSAGE)
        logger = get_logger("progress.case")
        logger.info("scraper.row_started", page=1, idx=1, console=green("pg 1 job 1 - "), end="")
        logger.info("scraper.job_inserted", job_id=42, console=green("INSERTED 42!"), end="")
        assert capsys.readouterr().out == f"{green('pg 1 job 1 - ')}{green('INSERTED 42!')}"

    def test_default_end_closes_the_open_line(self, console, capsys):
        configure_logging("closing", console=CONSOLE_MESSAGE)
        logger = get_logger("closing.case")
        logger.info("scraper.row_started", page=1, console=green("pg 1 job 1 - "), end="")
        logger.info("scraper.keyword_done", keyword="python", console=green("Done python"))
        assert capsys.readouterr().out == f"{green('pg 1 job 1 - ')}{green('Done python')}\n"

    def test_end_never_reaches_the_file(self, console, capsys):
        configure_logging("noend", console=CONSOLE_MESSAGE)
        get_logger("noend.case").info("scraper.row_started", page=1, console="pg 1 job 1 - ", end="")
        record = _events(log_file_path("noend"))[0]
        assert "end" not in record
        assert "_console_end" not in record

    def test_record_mode_keeps_one_record_per_line(self, console, capsys):
        configure_logging("lines", console=CONSOLE_RECORD)
        get_logger("lines.case").info("scraper.row_started", page=1, console=green("pg 1 job 1 - "), end="")
        assert capsys.readouterr().out == f"{green('pg 1 job 1 - ')}\n"

    def test_debug_records_need_log_level_10(self, console, capsys, monkeypatch):
        """The filtering bound logger drops `debug` before the console text is read."""
        configure_logging("level", console=CONSOLE_MESSAGE)
        get_logger("level.case").debug("scraper.row_started", page=1, console="pg 1 job 1 - ")
        assert capsys.readouterr().out == ""

    def test_end_without_console_text_writes_nothing(self, console, capsys):
        configure_logging("stray", console=CONSOLE_MESSAGE)
        get_logger("stray.case").info("scraper.row_started", page=1, end="")
        assert capsys.readouterr().out == ""

    def test_non_string_end_falls_back_to_newline(self, console, capsys):
        configure_logging("badend", console=CONSOLE_MESSAGE)
        get_logger("badend.case").info("scraper.row_started", console="pg 1 job 1 - ", end=0)
        assert capsys.readouterr().out == "pg 1 job 1 - \n"


class TestFileOnlyRecords:
    def test_message_mode_keeps_console_quiet(self, console, capsys):
        configure_logging("quiet", console=CONSOLE_MESSAGE)
        get_logger("quiet.case").info("sql.query_executed", rows=1)
        assert capsys.readouterr().out == ""
        assert _events(log_file_path("quiet"))[0]["event"] == "sql.query_executed"

    def test_record_mode_still_renders_the_record(self, console, capsys):
        configure_logging("rendered", console=CONSOLE_RECORD)
        get_logger("rendered.case").info("sql.query_executed", rows=1)
        out = stripAnsi(capsys.readouterr().out)
        assert "sql.query_executed" in out
        assert "rows=1" in out

    def test_record_mode_falls_back_to_json_without_color(self, console, capsys, monkeypatch):
        monkeypatch.setenv("LOG_COLOR", "False")
        configure_logging("json", console=CONSOLE_RECORD)
        get_logger("json.case").info("sql.query_executed", rows=1)
        assert json.loads(capsys.readouterr().out)["event"] == "sql.query_executed"


class TestMessageColumn:
    def test_message_is_the_first_named_field(self, console, capsys):
        """`message` is the sentence to read; rendering it first is the whole point of the column."""
        configure_logging("lead", console=CONSOLE_RECORD)
        get_logger("lead.case").info("timer.started", message="All jobs enriched.", wait_seconds=10)
        out = stripAnsi(capsys.readouterr().out)
        assert "timer.started" in out
        assert "message='All jobs enriched.'" in out
        assert out.count("All jobs enriched.") == 1
        assert out.index("message=") < out.index("wait_seconds=10")

    def test_message_renders_first_even_when_passed_last(self, console, capsys):
        """The position comes from the column, not from the call-site keyword order."""
        configure_logging("late", console=CONSOLE_RECORD)
        get_logger("late.case").info("jobs.skipped", limit=10, message="No skills pending.")
        out = stripAnsi(capsys.readouterr().out)
        assert "message='No skills pending.'" in out
        assert out.index("message=") < out.index("limit=10")

    def test_record_without_message_is_unchanged(self, console, capsys):
        configure_logging("nomessage", console=CONSOLE_RECORD)
        get_logger("nomessage.case").info("job.started", job_id=7, total=5653)
        out = stripAnsi(capsys.readouterr().out)
        assert "job.started" in out
        assert "job_id=7" in out


class TestColumnOrder:
    def test_app_tag_precedes_level_event_and_message(self, console, capsys):
        configure_logging("order", console=CONSOLE_RECORD)
        get_logger("order.case").info("jobs.skipped", message="All CV matches calculated.", reason="no_pending_jobs", wait_seconds=10)
        out = stripAnsi(capsys.readouterr().out)
        assert out.index("[order]") < out.index("[info") < out.index("jobs.skipped") < out.index("message=") < out.index("reason=") < out.index("wait_seconds=")

    def test_app_tag_precedes_level_without_message(self, console, capsys):
        configure_logging("tagno", console=CONSOLE_RECORD)
        get_logger("tagno.case").info("job.started", job_id=7)
        out = stripAnsi(capsys.readouterr().out)
        assert out.index("[tagno]") < out.index("[info") < out.index("job.started") < out.index("job_id=7")
