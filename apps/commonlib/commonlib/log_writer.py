"""JSONL file writing and rotation for `commonlib.observability`.

Kept apart from `observability` so the structlog configuration does not own file
handling. `observability` injects a `resolve_path` callable rather than this module
importing back, which keeps the dependency one-way.

Keys prefixed with `_` are treated as processor-private and never reach the file.

A write that fails (an unwritable log directory, typically a `data/` folder owned by
root because a container created it) is never fatal: `append_jsonl` logs
`logs.write_failed` once per path with a chown hint and drops the record, and re-arms
the warning after the next successful write. Losing a log line must never take down a
worker, but the failure must not be invisible either.

| Variable | Default | Meaning |
|---|---|---|
| `LOG_DIR` | `data/logs` | Directory holding the JSONL files |
| `LOG_FILE_MAX_BYTES` | `10485760` | Rotate the file once it grows past this |
| `LOG_FILE_BACKUP_COUNT` | `5` | Rotated files to keep |
"""
import json
import os
from collections.abc import Callable

from commonlib.environmentUtil import getEnv

DEFAULT_LOG_DIR = "data/logs"
DEFAULT_LOG_FILE_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_LOG_FILE_BACKUP_COUNT = 5
LEGACY_LOG_FILE_NAME = "app.jsonl"
PRIVATE_KEY_PREFIX = "_"
_warned_write_failures: set[str] = set()


def resolve_read_path(path: str) -> str | None:
    """Return the JSONL file to read for `path`, falling back to the legacy name.

    `configure_logging("<app>")` names the file after the app, but a module that logged
    before the app name was set wrote `app.jsonl` instead. Readers prefer the per-app
    file and fall back to that legacy name so existing history keeps rendering.
    """
    if os.path.isfile(path):
        return path
    legacy = os.path.join(os.path.dirname(path), LEGACY_LOG_FILE_NAME)
    return legacy if os.path.isfile(legacy) else None


def _env(primary: str, legacy: str, default):
    value = getEnv(primary, None)
    if value is None:
        value = getEnv(legacy, None)
    return default if value is None or value == "" else value


def get_log_dir() -> str:
    return _env("LOG_DIR", "AI_ENRICH_LOG_DIR", DEFAULT_LOG_DIR)


def file_max_bytes() -> int:
    return int(_env("LOG_FILE_MAX_BYTES", "AI_ENRICH_LOG_FILE_MAX_BYTES", DEFAULT_LOG_FILE_MAX_BYTES))


def file_backup_count() -> int:
    return int(_env("LOG_FILE_BACKUP_COUNT", "AI_ENRICH_LOG_FILE_BACKUP_COUNT", DEFAULT_LOG_FILE_BACKUP_COUNT))


def rotate_if_needed(filepath: str) -> None:
    """Shift `filepath.1..N` down one slot and start a fresh `filepath`."""
    backups = file_backup_count()
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) <= file_max_bytes():
            return
        for i in range(backups - 1, 0, -1):
            if os.path.exists(f"{filepath}.{i}"):
                os.replace(f"{filepath}.{i}", f"{filepath}.{i + 1}")
        os.replace(filepath, f"{filepath}.1")
    except OSError:
        pass


def append_jsonl(filepath: str, record: dict) -> None:
    """Append one record, warning once per path instead of failing the caller.

    The warning's own record goes back through this writer, so the path is marked
    before the `warning()` call: the recursive write fails again but stays silent,
    which is what keeps the failure non-fatal without an infinite loop. A later
    successful write clears the mark so a recurring failure is reported again.
    """
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
        _warned_write_failures.discard(filepath)
    except OSError as exc:
        if filepath not in _warned_write_failures:
            _warned_write_failures.add(filepath)
            _warn_write_failure(filepath, exc)


def _warn_write_failure(filepath: str, exc: OSError) -> None:
    from commonlib.observability import get_logger  # local: `observability` imports this module back
    target = os.path.dirname(filepath) or "."
    parent = os.path.dirname(target) or target
    get_logger("commonlib.log_writer").warning(
        "logs.write_failed", path=filepath, error=str(exc),
        hint=f"sudo chown -R $(id -u):$(id -g) {parent} {target}")


def public_record(event_dict: dict) -> dict:
    """Drop the `_`-prefixed keys processors use to hand data to each other.

    `observability` carries the raw console text under a private key so the JSONL
    never receives the color escape sequences, while the console renderer still
    receives the untouched text.
    """
    return {key: value for key, value in event_dict.items() if not key.startswith(PRIVATE_KEY_PREFIX)}


def make_jsonl_writer(resolve_path: Callable[[], str], stamp: Callable[[dict], None]):
    """Build the structlog processor that mirrors every record to `resolve_path()`.

    `stamp` receives the record just before it is written, so the caller owns the
    app-name field and the path stays a single source of truth.
    """

    def _writer(logger, method_name, event_dict):  # noqa: ARG001 - structlog processor signature
        stamp(event_dict)
        filepath = resolve_path()
        rotate_if_needed(filepath)
        append_jsonl(filepath, public_record(event_dict))
        return event_dict

    return _writer
