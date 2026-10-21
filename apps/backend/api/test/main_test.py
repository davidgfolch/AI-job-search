from fastapi.testclient import TestClient
import json
import logging
import socket
import threading
import time

import pytest
import uvicorn
from main import app
import services.watcher_matcher as matcher_module
from commonlib.watcher_notify import notify_watcher
from services.watcher_matcher import WatcherMatcher

client = TestClient(app)

def test_uvicorn_access_log_disabled():
    assert logging.getLogger("uvicorn.access").disabled

def test_get_timezone():
    response = client.get("/api/system/timezone")
    assert response.status_code == 200
    data = response.json()
    assert "offset_minutes" in data
    assert isinstance(data["offset_minutes"], int)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_logging_middleware_is_wired(log_records):
    response = client.get("/health")
    assert response.status_code == 200
    records = log_records(event="http.request_completed")
    assert len(records) == 1
    assert records[0]["method"] == "GET"
    assert records[0]["path"] == "/health"
    assert records[0]["status_code"] == 200
    assert records[0]["logger"] == "backend"
    assert records[0]["module"].endswith("middleware.request_logging")
    assert log_records(event="http.request_failed") == []


def test_request_logging_middleware_logs_error_status(log_records):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert log_records(event="http.request_completed")[0]["status_code"] == 404
    failed = log_records(event="http.request_failed")
    assert [record["level"] for record in failed] == ["warning"]
    assert failed[0]["path"] == "/api/does-not-exist"


# --- App-level integration: enrichment notification -> real route -> matcher ---
# The unit tests mock both sides; this pins the real wiring end to end. The app
# runs in a uvicorn thread, the notification uses the shared client
# (`commonlib.watcher_notify`) that `aiEnrich` calls after persisting a job, and
# the real `/api/jobs/notify-watcher` route feeds the real `WatcherMatcher` loop.
# Only the DB boundary is faked, so no MySQL/Ollama is needed and live data is
# never touched.

CONFIG_ID = 7
MATCHING_JOB_ID = 1001
UNKNOWN_JOB_ID = 999999


class FakeWatcherRepository:
    def __init__(self, existing_ids):
        self.existing_ids = set(existing_ids)
        self.existing_checks = []

    def get_recently_enriched_ids(self, since_minutes=10):
        return []

    def get_watched_configs(self):
        return [(CONFIG_ID, json.dumps({"ai_enriched": True}))]

    def get_existing_job_ids(self, job_ids):
        self.existing_checks.append(set(job_ids))
        return set(job_ids) & self.existing_ids

    def get_active_matches_for_jobs(self, job_ids):
        return []

    def match_jobs_against_config(self, config_id, where_part, job_ids):
        return sorted(job_ids)


class FakeWatcherMatchRepository:
    def __init__(self):
        self.matches = []

    def insert_match(self, config_id, job_id):
        self.matches.append((config_id, job_id))

    def insert_tombstone(self, config_id, job_id):
        pass

    def delete_active_matches_for_jobs(self, job_ids):
        pass

    def cleanup_old_rows(self, older_than_days=1):
        return 0


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until(predicate, timeout: float = 10, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


@pytest.fixture
def live_watcher(monkeypatch):
    WatcherMatcher.reset_for_testing()
    fake_repo = FakeWatcherRepository({MATCHING_JOB_ID})
    fake_match_repo = FakeWatcherMatchRepository()
    monkeypatch.setattr(matcher_module, "WatcherRepository", lambda: fake_repo)
    monkeypatch.setattr(matcher_module, "WatcherMatchRepository", lambda: fake_match_repo)
    monkeypatch.setattr(matcher_module, "POLL_INTERVAL_SECONDS", 0.05)

    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    assert _wait_until(lambda: server.started), "backend did not start"
    try:
        yield f"http://127.0.0.1:{port}", fake_repo, fake_match_repo
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        matcher_module.get_watcher_matcher().stop_background_matcher()
        WatcherMatcher.reset_for_testing()


def test_enrichment_notification_enqueues_and_matches_job(live_watcher):
    base_url, fake_repo, fake_match_repo = live_watcher

    assert notify_watcher([MATCHING_JOB_ID], base_url=base_url) is True

    assert _wait_until(lambda: fake_match_repo.matches), "matcher did not process the notification"
    assert fake_match_repo.matches == [(CONFIG_ID, MATCHING_JOB_ID)]
    assert any(MATCHING_JOB_ID in ids for ids in fake_repo.existing_checks)


def test_notification_for_missing_job_produces_no_match(live_watcher):
    base_url, fake_repo, fake_match_repo = live_watcher

    assert notify_watcher([UNKNOWN_JOB_ID], base_url=base_url) is True

    assert _wait_until(
        lambda: any(UNKNOWN_JOB_ID in ids for ids in fake_repo.existing_checks)
    ), "matcher never looked up the notified id"
    assert fake_match_repo.matches == []
