"""JSONL file writing and rotation for `commonlib.observability`.

Kept apart from `observability` so the structlog configuration does not own file
handling. `observability` injects a `resolve_path` callable rather than this module
importing back, which keeps the dependency one-way.

Keys prefixed with `_` are treated as processor-private and never reach the file.

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
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str, ensure_ascii=False) + "\n")
    except OSError:
        pass


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

    def _writer(logger, method_name, event_dict):
        stamp(event_dict)
        filepath = resolve_path()
        rotate_if_needed(filepath)
        append_jsonl(filepath, public_record(event_dict))
        return event_dict

    return _writer
