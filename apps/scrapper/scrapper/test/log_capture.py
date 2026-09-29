import contextlib
import json
from pathlib import Path

import structlog
from structlog.testing import capture_logs

from commonlib.observability import configure_logging, log_file_path

APP_NAME = "scrapper"
DEBUG_LEVEL = 10
CONSOLE_ONLY_FIELDS = ("console", "end")


@contextlib.contextmanager
def captured_records(module, module_name: str):
    """Yield the structlog records emitted by `module` at DEBUG level.

    `commonlib.observability.get_logger` returns a concrete bound logger that keeps the
    processor chain captured when it was built, so a test that needs `debug` events both
    swaps in a logger bound to the reconfigured chain and rebuilds it after
    `capture_logs` installs its capture processor. The original logger and the original
    structlog config are restored on exit.
    """
    previous_config = structlog.get_config()
    previous_logger = getattr(module, "logger", None)
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(DEBUG_LEVEL), cache_logger_on_first_use=False)
    try:
        with capture_logs() as entries:
            module.logger = structlog.get_logger().bind(module=module_name)
            yield entries
    finally:
        if previous_logger is not None:
            module.logger = previous_logger
        structlog.configure(**previous_config)


def read_records(app_name: str = APP_NAME):
    """Read the JSONL records the shared writer mirrored for `app_name`."""
    path = Path(log_file_path(app_name))
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@contextlib.contextmanager
def jsonl_records(tmp_path, monkeypatch, app_name: str = APP_NAME):
    """Point the JSONL writer at `tmp_path` and yield a reader for its records."""
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    configure_logging(app_name)
    yield lambda: read_records(app_name)


def structured_fields(kwargs: dict) -> dict:
    """Drop the presentational `console=`/`end=` fields from a recorded call."""
    return {key: value for key, value in kwargs.items() if key not in CONSOLE_ONLY_FIELDS}


def logged_calls(mock_logger, level: str, event: str) -> list:
    """Return the `mock_logger.<level>(event, ...)` calls recorded for `event`."""
    return [call for call in getattr(mock_logger, level).call_args_list if call.args and call.args[0] == event]


def assert_logged(mock_logger, level: str, event: str, **fields):
    """Assert a logger call carries exactly these structured fields.

    The restored console text is asserted separately with `assert_console_text`, so a
    change to the human wording does not hide a change to the machine fields.
    """
    calls = logged_calls(mock_logger, level, event)
    assert calls, f"{level}('{event}') was never called"
    recorded = [structured_fields(call.kwargs) for call in calls]
    assert fields in recorded, f"{level}('{event}') fields {recorded} do not include {fields}"


def assert_console_text(mock_logger, level: str, event: str, contains: str = "", end: str = "\n"):
    """Assert the console half of a record: its wording and whether the line stays open."""
    calls = logged_calls(mock_logger, level, event)
    assert calls, f"{level}('{event}') was never called"
    kwargs = calls[-1].kwargs
    assert contains in kwargs.get("console", ""), f"console={kwargs.get('console')!r} does not contain {contains!r}"
    assert kwargs.get("end", "\n") == end, f"end={kwargs.get('end')!r}, expected {end!r}"
