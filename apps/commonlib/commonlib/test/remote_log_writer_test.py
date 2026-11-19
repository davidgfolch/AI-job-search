import json
from unittest.mock import Mock, patch

import pytest

from commonlib import remote_log_writer as writer


@pytest.fixture(autouse=True)
def clean_sink(monkeypatch):
    monkeypatch.setattr(writer, "_config", None)
    monkeypatch.setattr(writer, "_buffer", [])


@pytest.mark.parametrize("url, expected", [
    (None, False),
    ("", False),
    ("http://localhost:8000", False),
    ("http://127.0.0.1:8000", False),
    ("http://127.0.0.2:8000", False),
    ("http://::1:8000", False),
    ("http://box.local:8000", True),
    ("http://192.168.1.20:8000", True),
    ("https://jobs.example.com", True),
])
def test_is_remote_url(url, expected):
    assert writer.is_remote_url(url) is expected


def test_local_backend_does_not_enable_shipping():
    assert writer.configure_remote_logging("http://localhost:8000", start_thread=False) is False
    assert writer._config is None


@pytest.mark.parametrize("discovered, expected", [
    (None, False),
    ("http://localhost:8000", False),
    ("http://192.168.1.20:8000/", True),
])
def test_discovered_backend_drives_shipping(discovered, expected):
    with patch.object(writer, "_discovered_backend_url", return_value=discovered):
        assert writer.configure_remote_logging(start_thread=False) is expected
    assert (writer._config is not None) is expected
    if expected:
        assert writer._config["base_url"] == "http://192.168.1.20:8000"


def test_explicit_base_url_skips_discovery():
    with patch.object(writer, "_discovered_backend_url") as discover:
        assert writer.configure_remote_logging("http://192.168.1.20:8000/", start_thread=False) is True
    discover.assert_not_called()
    assert writer._config["base_url"] == "http://192.168.1.20:8000"


def test_processor_batches_records(monkeypatch):
    monkeypatch.setenv(writer.BATCH_SIZE_ENV, "2")
    writer.configure_remote_logging("http://192.168.1.20:8000", start_thread=False)
    response = Mock(ok=True)
    with patch.object(writer.requests, "post", return_value=response) as post:
        for count in range(2):
            writer.remote_log_processor(None, "info", {"event": "scraper.job.inserted", "job_id": count, "logger": "scrapper"})
        post.assert_called_once()
        payload = json.loads(post.call_args.kwargs["data"])
        assert payload["app"] == "scrapper"
        assert [row["job_id"] for row in payload["records"]] == [0, 1]
    assert writer._buffer == []


def test_processor_drops_private_console_fields():
    writer.configure_remote_logging("http://192.168.1.20:8000", start_thread=False)
    writer.remote_log_processor(None, "info", {"event": "scraper.job.inserted", "logger": "scrapper", "_console": "colored"})
    assert "_console" not in writer._buffer[0]
    assert writer._buffer[0]["event"] == "scraper.job.inserted"


def test_processor_ignores_diagnostics_and_other_apps():
    writer.configure_remote_logging("http://192.168.1.20:8000", start_thread=False)
    writer.remote_log_processor(None, "warning", {"event": "remote_logs.failed", "logger": "scrapper"})
    writer.remote_log_processor(None, "info", {"event": "scraper.job.inserted", "logger": "backend"})
    assert writer._buffer == []


def test_failed_post_keeps_records_for_retry():
    writer.configure_remote_logging("http://192.168.1.20:8000", start_thread=False)
    writer._buffer.append({"event": "scraper.job.inserted"})
    with patch.object(writer.requests, "post", side_effect=OSError("offline")):
        with patch.object(writer, "_warning") as warning:
            writer.flush_remote_logs()
    warning.assert_called_once()
    assert len(writer._buffer) == 1


def test_rejected_post_keeps_records_for_retry():
    writer.configure_remote_logging("http://192.168.1.20:8000", start_thread=False)
    writer._buffer.append({"event": "scraper.job.inserted"})
    with patch.object(writer.requests, "post", return_value=Mock(ok=False, status_code=503)):
        writer.flush_remote_logs()
    assert len(writer._buffer) == 1


def test_buffer_stays_bounded(monkeypatch):
    monkeypatch.setenv(writer.BATCH_SIZE_ENV, "2")
    writer.configure_remote_logging("http://192.168.1.20:8000", start_thread=False)
    with patch.object(writer, "flush_remote_logs"):
        for count in range(20):
            writer.remote_log_processor(None, "info", {"event": "scraper.job.inserted", "job_id": count, "logger": "scrapper"})
    assert len(writer._buffer) <= 10
