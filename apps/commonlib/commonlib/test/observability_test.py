import os
import json
import structlog

from commonlib import observability
from commonlib.observability import configure_logging, get_logger, LOG_DIR, LOG_FILE_BACKUP_COUNT


def _reset():
    observability._configured = False


def test_configure_logging_idempotent():
    _reset()
    configure_logging("test")
    configure_logging("test")
    assert True


def test_get_logger_returns_bound_logger():
    _reset()
    logger = get_logger("test")
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


def test_get_logger_with_name():
    _reset()
    logger = get_logger("my.module")
    assert logger is not None


def test_structlog_configured():
    _reset()
    configure_logging("test")
    processors = structlog.get_config()["processors"]
    assert any("add_log_level" in str(p) for p in processors)


def test_log_writes_to_jsonl_file():
    _reset()
    configure_logging("test_jsonl")
    logger = get_logger("test_jsonl.case")
    log_file = os.path.join(LOG_DIR, "test_jsonl.jsonl")
    logger.info("test.event", key="value", num=42)
    assert os.path.exists(log_file)
    with open(log_file, encoding="utf-8") as f:
        line = f.readline().strip()
    entry = json.loads(line)
    assert entry["event"] == "test.event"
    assert entry["key"] == "value"
    assert entry["num"] == 42
    assert entry["level"] == "info"
    assert entry["logger"] == "test_jsonl"
    assert "timestamp" in entry
    os.remove(log_file)


def test_log_rotation():
    _reset()
    configure_logging("test_rotation")
    logger = get_logger("test_rotation.case")
    log_file = os.path.join(LOG_DIR, "test_rotation.jsonl")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("x" * 101)
    orig_max = observability.LOG_FILE_MAX_BYTES
    try:
        observability.LOG_FILE_MAX_BYTES = 100
        logger.info("after_rotate")
        assert os.path.exists(f"{log_file}.1")
    finally:
        observability.LOG_FILE_MAX_BYTES = orig_max
    if os.path.exists(f"{log_file}.1"):
        os.remove(f"{log_file}.1")
    if os.path.exists(log_file):
        os.remove(log_file)


def test_log_rotation_oserror():
    _reset()
    configure_logging("test_rotation_err")
    logger = get_logger("test_rotation_err.case")
    log_file = os.path.join(LOG_DIR, "test_rotation_err.jsonl")
    orig_max = observability.LOG_FILE_MAX_BYTES
    orig_backup = observability.LOG_FILE_BACKUP_COUNT
    try:
        observability.LOG_FILE_MAX_BYTES = 10
        observability.LOG_FILE_BACKUP_COUNT = 2
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("x" * 20)
        with patch("os.replace", side_effect=OSError("permission denied")):
            logger.info("rotation_error_test")
    finally:
        observability.LOG_FILE_MAX_BYTES = orig_max
        observability.LOG_FILE_BACKUP_COUNT = orig_backup
    if os.path.exists(log_file):
        os.remove(log_file)


def test_log_jsonl_write_oserror():
    _reset()
    configure_logging("test_write_err")
    logger = get_logger("test_write_err.case")
    log_file = os.path.join(LOG_DIR, "test_write_err.jsonl")
    orig_max = observability.LOG_FILE_MAX_BYTES
    try:
        observability.LOG_FILE_MAX_BYTES = 999999999
        with patch("builtins.open", side_effect=OSError("disk full")):
            logger.info("write_error_test")
    finally:
        observability.LOG_FILE_MAX_BYTES = orig_max
    if os.path.exists(log_file):
        os.remove(log_file)


from unittest.mock import patch
