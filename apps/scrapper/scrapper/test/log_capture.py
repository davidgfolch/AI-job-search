import contextlib
import json
from pathlib import Path

import structlog
from structlog.testing import capture_logs

from commonlib.observability import configure_logging, log_file_path

APP_NAME = "scrapper"
DEBUG_LEVEL = 10


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
