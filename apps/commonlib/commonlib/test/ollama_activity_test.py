import json
import threading
import time
from unittest.mock import patch

from commonlib import ollama_activity
from commonlib.ollama_activity import (
    HIGH_PRIORITY,
    LOW_PRIORITY,
    activity_dir,
    busy_seconds,
    is_busy,
    request_slot,
)


def _hold_slot(priority, ready, release, results):
    with request_slot(priority=priority, timeout=1) as acquired:
        results.append(acquired)
        ready.set()
        release.wait(2)


def _start_holder(priority):
    ready, release, results = threading.Event(), threading.Event(), []
    thread = threading.Thread(target=_hold_slot, args=(priority, ready, release, results), daemon=True)
    thread.start()
    assert ready.wait(2) is True
    return thread, release, results


def test_activity_dir_defaults_next_to_the_metrics_file(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_ENRICH_OLLAMA_ACTIVITY_DIR", raising=False)
    monkeypatch.setenv("AI_ENRICH_METRICS_FILE", str(tmp_path / "metrics" / "enrichment_metrics.json"))
    assert activity_dir() == tmp_path / "metrics" / "ollama_activity"


def test_activity_dir_honours_the_override(monkeypatch, tmp_path):
    target = tmp_path / "custom"
    monkeypatch.setenv("AI_ENRICH_OLLAMA_ACTIVITY_DIR", str(target))
    assert activity_dir() == target


def test_no_marker_means_idle():
    assert busy_seconds() is None
    assert is_busy() is False


def test_slot_writes_and_clears_the_busy_marker():
    with request_slot() as acquired:
        assert acquired is True
        assert is_busy() is True
    assert is_busy() is False


def test_stale_marker_is_ignored_and_removed():
    target = ollama_activity._marker_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"busy": True, "updated_at": time.time() - 3600}))
    assert busy_seconds(stale_after=1) is None
    assert target.exists() is False


def test_nested_slot_is_reentrant():
    with request_slot(priority=LOW_PRIORITY) as outer:
        with request_slot(priority=HIGH_PRIORITY) as inner:
            assert outer is True
            assert inner is True


def test_high_priority_shares_the_slot_with_high_priority():
    thread, release, results = _start_holder(HIGH_PRIORITY)
    try:
        with request_slot(priority=HIGH_PRIORITY, timeout=0.05) as acquired:
            assert acquired is True
    finally:
        release.set()
        thread.join(2)
    assert results == [True]


def test_low_priority_is_refused_while_high_priority_holds_the_slot():
    thread, release, results = _start_holder(HIGH_PRIORITY)
    try:
        with request_slot(priority=LOW_PRIORITY, timeout=0.05) as acquired:
            assert acquired is False
    finally:
        release.set()
        thread.join(2)
    assert results == [True]


def test_low_priority_is_refused_while_low_priority_holds_the_slot():
    thread, release, results = _start_holder(LOW_PRIORITY)
    try:
        with request_slot(priority=LOW_PRIORITY, timeout=0.05) as acquired:
            assert acquired is False
    finally:
        release.set()
        thread.join(2)
    assert results == [True]


def test_high_priority_waits_for_a_low_priority_holder(monkeypatch):
    monkeypatch.setattr(ollama_activity, "POLL_SECONDS", 0.01)
    thread, release, results = _start_holder(LOW_PRIORITY)
    threading.Timer(0.05, release.set).start()
    try:
        with request_slot(priority=HIGH_PRIORITY, timeout=2) as acquired:
            assert acquired is True
    finally:
        release.set()
        thread.join(2)
    assert results == [True]


@patch("commonlib.ollama_activity.logger")
def test_high_priority_fails_open_when_the_low_holder_is_stuck(mock_logger, monkeypatch):
    monkeypatch.setattr(ollama_activity, "POLL_SECONDS", 0.01)
    thread, release, results = _start_holder(LOW_PRIORITY)
    try:
        with request_slot(priority=HIGH_PRIORITY, timeout=0.02) as acquired:
            assert acquired is True
    finally:
        release.set()
        thread.join(2)
    assert results == [True]
    mock_logger.warning.assert_called_once_with("ollama.slot.timeout", timeout=0.02)
