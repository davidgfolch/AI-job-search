import json
import os
import tempfile

import pytest

from commonlib.services.metrics_collector import MetricsCollector, METRICS_FILE, ROLLING_WINDOW


@pytest.fixture(autouse=True)
def reset_singleton():
    MetricsCollector._instance = None
    yield


@pytest.fixture
def collector():
    return MetricsCollector()


def test_singleton(collector):
    c2 = MetricsCollector()
    assert collector is c2


def test_record_job_success(collector):
    collector.record_job("test_module", 1.5, success=True)
    m = collector._modules["test_module"]
    assert m["jobs_processed"] == 1
    assert m["jobs_succeeded"] == 1
    assert m["jobs_failed"] == 0
    assert m["total_duration"] == 1.5
    assert len(m["durations"]) == 1
    assert m["durations"][0] == 1.5


def test_record_job_failure(collector):
    collector.record_job("test_module", 2.0, success=False)
    m = collector._modules["test_module"]
    assert m["jobs_processed"] == 1
    assert m["jobs_failed"] == 1
    assert m["jobs_succeeded"] == 0


def test_record_error(collector):
    collector.record_error("test_module", "something went wrong")
    m = collector._modules["test_module"]
    assert m["last_error"] == "something went wrong"
    assert m["last_error_at"] is not None


def test_set_pending(collector):
    collector.set_pending("test_module", 42)
    assert collector._modules["test_module"]["pending_jobs"] == 42


def test_get_snapshot_no_data(collector):
    snapshot = collector.get_snapshot()
    assert "timestamp" in snapshot
    assert snapshot["modules"] == {}
    assert snapshot["global"]["total_jobs"] == 0
    assert snapshot["global"]["total_errors"] == 0


def test_get_snapshot_with_data(collector):
    for _ in range(10):
        collector.record_job("mod_a", 1.0, True)
        collector.record_job("mod_b", 2.0, False)
    snapshot = collector.get_snapshot()
    assert snapshot["modules"]["mod_a"]["jobs_processed"] == 10
    assert snapshot["modules"]["mod_a"]["p50"] == 1.0
    assert snapshot["modules"]["mod_b"]["p50"] == 2.0
    assert snapshot["global"]["total_jobs"] == 20
    assert snapshot["global"]["total_errors"] == 10


def test_rolling_window(collector):
    for _ in range(ROLLING_WINDOW + 50):
        collector.record_job("mod", 0.5, True)
    assert len(collector._modules["mod"]["durations"]) == ROLLING_WINDOW


def test_persist_and_load(collector):
    collector.record_job("mod_x", 3.0, True)
    collector.set_pending("mod_x", 5)
    collector.record_error("mod_y", "err")
    collector.persist()

    path = METRICS_FILE
    assert os.path.exists(path)
    with open(path) as f:
        data = json.load(f)
    assert "modules" in data
    assert data["modules"]["mod_x"]["jobs_processed"] == 1

    MetricsCollector._instance = None
    c2 = MetricsCollector()
    assert c2._modules["mod_x"]["jobs_processed"] == 1
    assert c2._modules["mod_x"]["pending_jobs"] == 5
    assert c2._modules["mod_y"]["last_error"] == "err"

    os.remove(path)


def test_load_corrupted_file(collector):
    path = METRICS_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("not json")
    MetricsCollector._instance = None
    c2 = MetricsCollector()
    assert c2._modules == {}
    os.remove(path)
