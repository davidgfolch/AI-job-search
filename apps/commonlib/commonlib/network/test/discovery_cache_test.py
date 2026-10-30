"""Tests for the shared discovery cache: TTLs, cross-process lock and cached_discover."""
import json
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from commonlib.network import discovery_cache as cache


def _write_raw(payload):
    path = cache.cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestCachePath:
    def test_env_override(self, monkeypatch, tmp_path):
        target = tmp_path / "custom" / "cache.json"
        monkeypatch.setenv("COMMONLIB_DISCOVERY_CACHE", str(target))
        assert cache.cache_path() == target

    def test_default_lives_under_the_repo_data_dir(self, monkeypatch):
        monkeypatch.delenv("COMMONLIB_DISCOVERY_CACHE", raising=False)
        assert cache.cache_path() == cache.DEFAULT_CACHE_PATH
        assert cache.cache_path().parent.name == "discovery"


class TestReadEntry:
    def test_missing_file(self):
        assert cache.read_entry("mysql") is None

    @pytest.mark.parametrize("payload", [
        "not json at all",
        {"version": 1, "entries": []},
        {"version": 1, "entries": {"mysql": "10.0.0.1"}},
        {"version": 1, "entries": {"mysql": {"host": "10.0.0.1", "ts": "yesterday"}}},
    ], ids=["invalid-json", "entries-not-dict", "entry-not-dict", "bad-timestamp"])
    def test_malformed_payload_is_ignored(self, payload):
        if isinstance(payload, str):
            path = cache.cache_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        else:
            _write_raw(payload)
        assert cache.read_entry("mysql") is None

    def test_fresh_positive_entry(self):
        cache.write_entry("mysql", "10.0.0.1")
        assert cache.read_entry("mysql")["host"] == "10.0.0.1"

    def test_expired_positive_entry(self, monkeypatch):
        cache.write_entry("mysql", "10.0.0.1")
        monkeypatch.setattr(cache, "POSITIVE_TTL", -1)
        assert cache.read_entry("mysql") is None

    def test_fresh_negative_entry(self):
        cache.write_entry("mysql", None)
        assert cache.read_entry("mysql")["host"] is None

    def test_expired_negative_entry(self, monkeypatch):
        cache.write_entry("mysql", None)
        monkeypatch.setattr(cache, "NEGATIVE_TTL", -1)
        assert cache.read_entry("mysql") is None

    def test_positive_and_negative_ttls_differ(self, monkeypatch):
        monkeypatch.setattr(cache, "POSITIVE_TTL", 10)
        monkeypatch.setattr(cache, "NEGATIVE_TTL", 1000)
        cache.write_entry("mysql", None)
        assert cache.read_entry("mysql") is not None
        cache.write_entry("mysql", "10.0.0.1")
        assert cache.read_entry("mysql") is not None


class TestWriteAndClear:
    def test_write_keeps_other_kinds(self):
        cache.write_entry("mysql", "10.0.0.1")
        cache.write_entry("ollama", "10.0.0.2")
        assert cache.read_entry("mysql")["host"] == "10.0.0.1"
        assert cache.read_entry("ollama")["host"] == "10.0.0.2"

    def test_write_is_versioned(self):
        cache.write_entry("mysql", "10.0.0.1")
        assert json.loads(cache.cache_path().read_text(encoding="utf-8"))["version"] == cache.CACHE_VERSION

    def test_unwritable_cache_logs_and_continues(self, monkeypatch):
        monkeypatch.setattr(cache, "_load", lambda: {})
        with patch("commonlib.network.discovery_cache.os.replace", side_effect=OSError("read-only")):
            cache.write_entry("mysql", "10.0.0.1")

    def test_clear_removes_only_that_kind(self):
        cache.write_entry("mysql", "10.0.0.1")
        cache.write_entry("ollama", "10.0.0.2")
        cache.clear("mysql")
        assert cache.read_entry("mysql") is None
        assert cache.read_entry("ollama")["host"] == "10.0.0.2"


class TestScanLock:
    def test_acquired_then_released(self):
        with cache.scan_lock("mysql") as acquired:
            assert acquired is True
            assert cache._lock_path("mysql").exists()
        assert not cache._lock_path("mysql").exists()

    def test_contended_lock_times_out(self):
        with cache.scan_lock("mysql") as acquired:
            assert acquired is True
            with cache.scan_lock("mysql", timeout=0) as second:
                assert second is False
        assert not cache._lock_path("mysql").exists()

    def test_stale_lock_is_taken_over(self):
        lock = cache._lock_path("mysql")
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("", encoding="utf-8")
        os.utime(lock, (time.time() - 1000, time.time() - 1000))
        with cache.scan_lock("mysql", timeout=0) as acquired:
            assert acquired is True

    def test_unwritable_lock_dir_still_scans(self):
        with patch("commonlib.network.discovery_cache.os.open", side_effect=PermissionError("ro")):
            with cache.scan_lock("mysql") as acquired:
                assert acquired is True


class TestCachedDiscover:
    def test_positive_cache_hit_skips_the_scan(self):
        cache.write_entry("mysql", "10.0.0.1")
        scan, verify, log = MagicMock(), MagicMock(return_value=True), MagicMock()
        assert cache.cached_discover("mysql", verify=verify, scan=scan, log=log) == "10.0.0.1"
        scan.assert_not_called()
        assert log.info.call_args[0][0] == "discovery.cache_hit"

    def test_unverifiable_cache_entry_triggers_a_scan(self):
        cache.write_entry("mysql", "10.0.0.1")
        verify = MagicMock(side_effect=[False, True])
        assert cache.cached_discover("mysql", verify=verify, scan=MagicMock(return_value=["10.0.0.9"])) == "10.0.0.9"
        assert cache.read_entry("mysql")["host"] == "10.0.0.9"

    def test_negative_cache_skips_the_scan(self):
        cache.write_entry("mysql", None)
        scan, log = MagicMock(), MagicMock()
        assert cache.cached_discover("mysql", verify=MagicMock(), scan=scan, log=log) is None
        scan.assert_not_called()
        assert log.info.call_args[0][0] == "discovery.cache_negative"

    def test_scan_result_is_verified_and_cached(self):
        scan = MagicMock(return_value=["10.0.0.1", "10.0.0.2"])
        verify = MagicMock(side_effect=[False, True])
        assert cache.cached_discover("mysql", verify=verify, scan=scan) == "10.0.0.2"

    def test_no_verified_candidate_is_negatively_cached(self):
        scan, log = MagicMock(return_value=["10.0.0.1"]), MagicMock()
        assert cache.cached_discover("mysql", verify=MagicMock(return_value=False), scan=scan, log=log) is None
        assert cache.read_entry("mysql")["host"] is None
        assert log.info.call_args[0][0] == "discovery.scan_no_result"

    def test_tried_hosts_are_never_verified(self):
        cache.write_entry("mysql", "10.0.0.1")
        scan = MagicMock(return_value=["10.0.0.1", "10.0.0.2"])
        verify = MagicMock(return_value=True)
        assert cache.cached_discover("mysql", verify=verify, scan=scan, tried={"10.0.0.1"}) == "10.0.0.2"
        verify.assert_called_once_with("10.0.0.2")

    def test_lock_timeout_reuses_what_the_other_process_wrote(self, monkeypatch):
        monkeypatch.setattr(cache, "LOCK_TIMEOUT", 0.0)
        entry = {"host": "10.0.0.1", "ts": time.time()}
        with cache.scan_lock("mysql"):
            with patch.object(cache, "read_entry", side_effect=[None, entry]):
                assert cache.cached_discover("mysql", verify=MagicMock(return_value=True), scan=MagicMock()) == "10.0.0.1"
