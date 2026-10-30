"""Persistent discovery cache shared by every process and container.

A LAN scan (three /24s, ~750 TCP connects) is expensive and used to run on every
cold start — five containers starting together ran five of them, and every
failed retry ran another. This module keeps the last verified host per service
kind in a JSON file that all containers mount, and takes a cross-platform file
lock so concurrent starts perform one scan and the rest reuse its result.

A negative entry is cached too, with a much shorter TTL: a down server is not
re-scanned by every retry, but is retried soon instead of being remembered
forever.
"""
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from commonlib.environmentUtil import ENV_PATH
from commonlib.observability import get_logger

logger = get_logger("commonlib.network.discovery_cache")

CACHE_VERSION = 1
POSITIVE_TTL = int(os.getenv("COMMONLIB_DISCOVERY_CACHE_SECONDS", "3600"))
NEGATIVE_TTL = int(os.getenv("COMMONLIB_DISCOVERY_NEGATIVE_CACHE_SECONDS", "60"))
LOCK_TIMEOUT = float(os.getenv("COMMONLIB_DISCOVERY_LOCK_SECONDS", "120"))
LOCK_STALE = float(os.getenv("COMMONLIB_DISCOVERY_LOCK_STALE_SECONDS", "300"))
DEFAULT_CACHE_PATH = ENV_PATH.parent / "data" / "discovery" / "cache.json"


def cache_path() -> Path:
    """Where the shared cache lives (`COMMONLIB_DISCOVERY_CACHE` overrides it)."""
    return Path(os.getenv("COMMONLIB_DISCOVERY_CACHE", "") or DEFAULT_CACHE_PATH)


def _load() -> dict:
    try:
        with open(cache_path(), encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", {}) if isinstance(data, dict) else {}
        return entries if isinstance(entries, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(entries: dict) -> None:
    path = cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"version": CACHE_VERSION, "entries": entries}, f)
        os.replace(tmp, path)
    except OSError as e:
        logger.debug("discovery.cache_write_failed", path=str(path), error=str(e))


def read_entry(kind: str) -> dict | None:
    """Fresh cache entry for `kind` (`{"host": ...}`), or None when missing/expired."""
    entry = _load().get(kind)
    if not isinstance(entry, dict):
        return None
    ttl = POSITIVE_TTL if entry.get("host") else NEGATIVE_TTL
    try:
        age = time.time() - float(entry.get("ts", 0))
    except (TypeError, ValueError):
        return None
    return entry if age <= ttl else None


def write_entry(kind: str, host: str | None) -> None:
    entries = _load()
    entries[kind] = {"host": host, "ts": time.time()}
    _save(entries)


def clear(kind: str) -> None:
    entries = _load()
    if entries.pop(kind, None) is not None:
        _save(entries)


def _lock_path(kind: str) -> Path:
    return cache_path().with_suffix(f".{kind}.lock")


def _is_stale(path: Path) -> bool:
    try:
        return time.time() - path.stat().st_mtime > LOCK_STALE
    except OSError:
        return True


@contextmanager
def scan_lock(kind: str, timeout: float | None = None):
    """Yield True when this process owns the scan lock, False when it timed out.

    With the lock held by another process the caller should wait for, then read,
    the cache instead of scanning a second time."""
    path = _lock_path(kind)
    deadline = time.time() + (LOCK_TIMEOUT if timeout is None else timeout)
    acquired = False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        while True:
            try:
                os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                acquired = True
                break
            except FileExistsError:
                if _is_stale(path):
                    _unlink(path)
                    continue
                if time.time() >= deadline:
                    break
                time.sleep(0.2)
            except OSError:
                # Cache directory not writable (read-only mount): scan anyway,
                # just without sharing the result.
                acquired = True
                break
        yield acquired
    finally:
        if acquired:
            _unlink(path)


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def cached_discover(kind: str, verify, scan, log=None, tried=()) -> str | None:
    """Resolve `kind` from the cache or a single, lock-guarded LAN scan.

    `verify(host)` decides whether a cached/ scanned host still serves the
    service; `scan()` performs the actual scan and returns candidate hosts in
    preference order. Hosts in `tried` were already probed by the caller and are
    not verified again."""
    log = log or logger
    tried = set(tried)
    entry = read_entry(kind)
    if entry is not None:
        host = entry.get("host")
        if host is None:
            log.info("discovery.cache_negative", kind=kind, ttl_secs=NEGATIVE_TTL)
            return None
        if host not in tried and verify(host):
            log.info("discovery.cache_hit", kind=kind, host=host)
            return host
        clear(kind)
    with scan_lock(kind) as acquired:
        if not acquired:
            log.info("discovery.scan_lock_timeout", kind=kind, lock_secs=LOCK_TIMEOUT)
            entry = read_entry(kind)
            host = entry.get("host") if entry else None
            return host if host and verify(host) else None
        entry = read_entry(kind)
        if entry and entry.get("host") and entry["host"] not in tried and verify(entry["host"]):
            log.info("discovery.cache_hit", kind=kind, host=entry["host"])
            return entry["host"]
        candidates = [host for host in scan() if host not in tried]
        for host in candidates:
            if verify(host):
                write_entry(kind, host)
                log.info("discovery.lan_discovered", kind=kind, host=host)
                return host
        write_entry(kind, None)
        log.info("discovery.scan_no_result", kind=kind, candidates=len(candidates))
        return None
