"""Cross-process inference slot shared by the Ollama workers.

`aiEnrich` and `aiEnrichSkill` are separate processes (usually containers) that use the
same Ollama server. They share the host directory that holds the metrics file, and this
module turns it into a single inference slot:

- normal work (the enrichment loops) holds a *shared* lock, so the workers never
  serialize against each other;
- the low-priority learning-path backfill needs an *exclusive* lock, so it only starts
  when no other request is in flight and never overlaps one.

Every request also leaves a small busy marker, which keeps the activity visible and lets
the backfill report how long the model has been busy. If the shared directory is not
usable (permissions, exotic filesystem) the slot degrades to the marker only.
"""
import json
import os
import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger

logger = get_logger("commonlib.ollama_activity")

HIGH_PRIORITY = "high"
LOW_PRIORITY = "low"
STALE_SECONDS = 300
SLOT_WAIT_SECONDS = 60
POLL_SECONDS = 1.0
LOCK_NAME = "ollama_inference.lock"

_local = threading.local()


def activity_dir() -> Path:
    configured = getEnv("AI_ENRICH_OLLAMA_ACTIVITY_DIR", "")
    if configured.strip():
        return Path(configured)
    metrics_file = getEnv("AI_ENRICH_METRICS_FILE", os.path.join("data", "metrics", "enrichment_metrics.json"))
    return Path(metrics_file).parent / "ollama_activity"


def _marker_file() -> Path:
    return activity_dir() / f"{socket.gethostname()}-{os.getpid()}.json"


def _write_marker(busy: bool) -> None:
    target = _marker_file()
    tmp = target.with_name(f"{target.name}.{threading.get_ident()}.tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({"busy": busy, "updated_at": time.time()}))
        os.replace(tmp, target)
    except OSError as exc:
        logger.debug("ollama.activity.write_failed", error=str(exc))


def busy_seconds(stale_after: float = STALE_SECONDS) -> float | None:
    """How long the newest in-flight request has been running, or None when the model is free."""
    now = time.time()
    newest = None
    for path in activity_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text())
            age = now - float(data.get("updated_at") or 0)
        except (OSError, ValueError):
            continue
        if age > stale_after:
            _discard(path)
            continue
        if data.get("busy") and (newest is None or age < newest):
            newest = age
    return newest


def is_busy(stale_after: float = STALE_SECONDS) -> bool:
    return busy_seconds(stale_after) is not None


def _discard(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _lock_path() -> Path:
    return activity_dir() / LOCK_NAME


def _try_lock(fd: int, shared: bool) -> bool:
    try:
        import fcntl
    except ImportError:  # Windows hosts: exclusive locking only, still correct but stricter
        return _try_lock_windows(fd)
    flags = (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB
    try:
        fcntl.flock(fd, flags)
        return True
    except OSError:
        return False


def _try_lock_windows(fd: int) -> bool:
    try:
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        return True
    except (ImportError, OSError):
        return False


def _unlock(fd: int) -> None:
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)
        return
    except ImportError:
        pass
    except OSError:
        return
    try:
        import msvcrt
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except (ImportError, OSError):
        pass


def _acquire(fd: int, shared: bool, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        if _try_lock(fd, shared):
            return True
        if not shared:
            return False
        if time.monotonic() >= deadline:
            # Never stall the priority workload on a stuck low-priority request.
            logger.warning("ollama.slot.timeout", timeout=timeout)
            return True
        time.sleep(POLL_SECONDS)


def _open_slot(shared: bool, timeout: float) -> tuple[bool, int | None]:
    try:
        path = _lock_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    except OSError as exc:
        logger.debug("ollama.slot.unavailable", error=str(exc))
        return True, None
    if _acquire(fd, shared, timeout):
        return True, fd
    os.close(fd)
    return False, None


def _enter() -> bool:
    """Returns True when this call nests inside a slot already held by this thread."""
    depth = getattr(_local, "depth", 0)
    _local.depth = depth + 1
    return depth > 0


def _leave() -> None:
    _local.depth = getattr(_local, "depth", 1) - 1


@contextmanager
def request_slot(priority: str = HIGH_PRIORITY, timeout: float = SLOT_WAIT_SECONDS) -> Iterator[bool]:
    """Hold the inference slot for the duration of the block.

    High priority shares the slot and only waits (bounded, fail-open) while a low-priority
    request is using the model. Low priority never waits: it yields False when anybody
    else holds the slot, so the caller can defer its work to a later idle moment.
    """
    if _enter():
        try:
            yield True
        finally:
            _leave()
        return
    try:
        acquired, fd = _open_slot(priority == HIGH_PRIORITY, timeout)
        if acquired:
            _write_marker(True)
        try:
            yield acquired
        finally:
            if acquired:
                _write_marker(False)
            if fd is not None:
                _unlock(fd)
                os.close(fd)
    finally:
        _leave()
