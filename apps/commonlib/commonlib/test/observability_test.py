import structlog

from commonlib.observability import configure_logging, get_logger


def test_configure_logging_idempotent():
    configure_logging()
    configure_logging()
    assert True


def test_get_logger_returns_bound_logger():
    logger = get_logger("test")
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


def test_get_logger_with_name():
    logger = get_logger("my.module")
    assert logger is not None


def test_structlog_configured():
    configure_logging()
    processors = structlog.get_config()["processors"]
    assert any("add_log_level" in str(p) for p in processors)
