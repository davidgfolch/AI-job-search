"""Shared structured logging for every app in the monorepo.

One structlog configuration serves all modules. Each app calls
`configure_logging("<app>")` from its entrypoint, before any `get_logger()` call, so
that its JSONL file is named after the app rather than the provisional default. The
provisional default is unavoidable because shared modules such as
`commonlib.sql.query_executor` build their logger at import time, which happens before
the entrypoint runs. The writer therefore resolves the app name on every record, so an
explicit `configure_logging()` always wins no matter when it is called.

Records are JSON lines with a dotted `domain.action` event name and `key=value`
fields. Callers never interpolate into the event name and never pass f-strings, so
records stay queryable:

    logger.warning("job.retry", attempt=2, delay=3, base_url=url)

Console output goes to stdout, and every record is mirrored to a JSONL file under
`LOG_DIR` named after the app. Configuration environment variables, all shared with
`commonlib.log_writer`; the `AI_ENRICH_*` names predate the modules that share this
library and are read as deprecated aliases.

| Variable | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `20` | 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR |
| `LOG_COLOR` | `True` | Colored console output instead of raw JSON on stdout |
| `LOG_DIR` | `data/logs` | Directory holding the JSONL files |
| `LOG_APP_NAME` | `app` | Provisional app name, used until an entrypoint sets one |
| `LOG_CONSOLE_MODE` | `record` | `record` renders each record, `message` prints only `console=` text |

## Two console modes

An app that wants a human console keeps the structured records for its JSONL and
passes the text to print through the `console` field:

    logger.info("scraper.page_loaded", page=3, total=10,
                console=green(f"{timestamp} - Starting page 3 of 10"))

`CONSOLE_RECORD` (the default) renders every record on stdout, while
`CONSOLE_MESSAGE` prints only the `console=` text and keeps the rest file-only, which
is how the scrapper shows its old-style output while the JSONL keeps every structured
record. Both live in `commonlib.console_render`; see that module for the details.

The mode is resolved on every record, not when structlog is configured, so an
entrypoint can select it after a shared module already logged. `LOG_LEVEL` is read when
structlog is configured and structlog freezes it on the first log call of each logger,
so an entrypoint must call `configure_logging()` before any other module logs.
"""
import os

import structlog

from commonlib.console_render import CONSOLE_MESSAGE, CONSOLE_RECORD, color_enabled, console_mode, render_console, set_console_mode, split_console_text
from commonlib.environmentUtil import getEnv
from commonlib.log_writer import get_log_dir, make_jsonl_writer

DEFAULT_LOG_LEVEL = 20
DEFAULT_APP_NAME = "app"

_app_name: str | None = None
_configured = False


def _env(primary: str, legacy: str, default):
    value = getEnv(primary, None)
    if value is None:
        value = getEnv(legacy, None)
    return default if value is None or value == "" else value


def get_app_name() -> str:
    return _app_name or _env("LOG_APP_NAME", "AI_ENRICH_LOG_APP_NAME", DEFAULT_APP_NAME)


def log_file_path(app_name: str | None = None) -> str:
    return os.path.join(get_log_dir(), f"{app_name or get_app_name()}.jsonl")


def _stamp_app_name(event_dict: dict) -> None:
    event_dict["logger"] = get_app_name()


def configure_logging(app_name: str | None = None, console: str | None = None) -> str:
    """Configure structlog once and name the JSONL output after `app_name`.

    Safe to call repeatedly and safe to call after shared modules have already built
    their loggers: only the first call configures structlog, later calls just re-point
    the writer and the console mode, and both are read per record. Returns the
    effective app name.

    `console` selects the mode, `CONSOLE_RECORD` (default) or `CONSOLE_MESSAGE`.
    """
    global _app_name, _configured
    if app_name:
        _app_name = app_name
    if console:
        set_console_mode(console)
    if _configured:
        return get_app_name()
    _configured = True
    level = int(_env("LOG_LEVEL", "AI_ENRICH_LOG_LEVEL", DEFAULT_LOG_LEVEL))
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.processors.format_exc_info,
            structlog.processors.dict_tracebacks,
            split_console_text,
            make_jsonl_writer(log_file_path, _stamp_app_name),
            render_console,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return get_app_name()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a logger that stamps every record with `name` in its `module` field.

    The name is bound explicitly because `structlog.get_logger(name)` passes it to the
    logger factory, and `PrintLoggerFactory` discards it.
    """
    configure_logging()
    return structlog.get_logger().bind(module=name)
