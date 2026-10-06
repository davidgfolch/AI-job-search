"""Console rendering for `commonlib.observability`.

The JSONL file is the machine-readable timeline, and the console is what a person
watches. These two can disagree, so a call site passes the human line through the
`console` field and keeps the structured fields for the file:

    logger.info("scraper.page_loaded", page=3, total=10,
                console=green(f"{timestamp} - Starting page 3 of 10"))

| Mode | Console | File |
|---|---|---|
| `CONSOLE_RECORD` (default) | `console=` text if present, otherwise the rendered record | every record |
| `CONSOLE_MESSAGE` | `console=` text only, no timestamp, level or event name | every record |

`CONSOLE_MESSAGE` is how an app keeps a quiet console: a record without `console=` is
written to the JSONL and never reaches stdout, which also hides the chatter from the
shared `commonlib` modules the app imports. The scrapper is the reference
implementation.

The raw text never reaches the file. `split_console_text` runs before the JSONL writer,
stores the ANSI-stripped text as `message` and hands the untouched text to the renderer
under the private `RAW_CONSOLE_KEY`, which `commonlib.log_writer` drops. With
`LOG_COLOR=False` the console text is stripped as well.

`end=""` reproduces a `print(..., end="")` progress prefix, so a line the old console
built from several records still reads the same while every part of it stays in the
JSONL. It only applies to `CONSOLE_MESSAGE`: `CONSOLE_RECORD` always ends the rendered
record with a newline, which keeps one record per line there.

The mode is resolved per record instead of when structlog is configured, so an
entrypoint can select it after a shared module already logged:
`commonlib.sql.query_executor` and `commonlib.ollama_client` build their loggers at
import time, before the entrypoint runs.

`CONSOLE_RECORD` renders `message` as the first named field, right after the
timestamp/level/event/`[logger]` prefix, so a human phrase is never buried in the middle
of the field list no matter where the call put it; records without `message` render
exactly as before. The renderer only affects stdout, never the JSONL.
"""
import sys

import structlog

from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.terminalColor import stripAnsi

CONSOLE_RECORD = "record"
CONSOLE_MESSAGE = "message"
CONSOLE_FIELD = "console"
CONSOLE_END_FIELD = "end"
RAW_CONSOLE_KEY = "_console"
RAW_CONSOLE_END_KEY = "_console_end"
DEFAULT_CONSOLE_MODE = CONSOLE_RECORD

_console_mode: str | None = None
# `message` is the human half of a record: keep it as the first named field, right after
# the timestamp/level/event/[logger] prefix, wherever the call placed it.
_BASE_RENDERER = structlog.dev.ConsoleRenderer()
_MESSAGE_COLUMN = structlog.dev.Column("message", _BASE_RENDERER._default_column_formatter)
_CONSOLE_RENDERER = structlog.dev.ConsoleRenderer(columns=[*_BASE_RENDERER.columns, _MESSAGE_COLUMN])
_JSON_RENDERER = structlog.processors.JSONRenderer()


def _env(primary: str, legacy: str, default: str) -> str:
    return getEnv(primary, None) or getEnv(legacy, None) or default


def color_enabled() -> bool:
    return getEnvBool("LOG_COLOR", getEnvBool("AI_ENRICH_LOG_COLOR", True))


def console_mode() -> str:
    """Return the console mode in effect: `CONSOLE_RECORD` or `CONSOLE_MESSAGE`."""
    return _console_mode or _env("LOG_CONSOLE_MODE", "AI_ENRICH_LOG_CONSOLE_MODE", DEFAULT_CONSOLE_MODE)


def set_console_mode(mode: str | None) -> None:
    global _console_mode
    _console_mode = mode or None


def split_console_text(logger, method_name, event_dict: dict) -> dict:
    """Move the `console` field to a private key and record the stripped text.

    `end` defaults to a newline and only travels with the console text, so a record
    without `console=` drops it instead of writing a stray newline to stdout.
    """
    raw = event_dict.pop(CONSOLE_FIELD, None)
    end = event_dict.pop(CONSOLE_END_FIELD, "\n")
    if raw is not None:
        text = raw if isinstance(raw, str) else str(raw)
        event_dict.setdefault("message", stripAnsi(text))
        event_dict[RAW_CONSOLE_KEY] = text
        event_dict[RAW_CONSOLE_END_KEY] = end if isinstance(end, str) else "\n"
    return event_dict


def render_console(logger, method_name, event_dict):
    """Print the `console` text, or render/drop the record, then stop the chain.

    Always raises `structlog.DropEvent` because `structlog.PrintLogger` prints whatever
    the last processor returns, and returning `None` is not silence.
    """
    raw = event_dict.pop(RAW_CONSOLE_KEY, None)
    if raw is not None:
        end = event_dict.pop(RAW_CONSOLE_END_KEY, "\n")
        if console_mode() != CONSOLE_MESSAGE:
            end = "\n"
        sys.stdout.write(f"{raw if color_enabled() else stripAnsi(raw)}{end}")
        sys.stdout.flush()
        raise structlog.DropEvent
    if console_mode() == CONSOLE_MESSAGE:
        raise structlog.DropEvent
    return (_CONSOLE_RENDERER if color_enabled() else _JSON_RENDERER)(logger, method_name, event_dict)
