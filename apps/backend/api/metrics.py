import os
import threading
import time

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.prometheus_exporter import build_prometheus_metrics, build_log_metrics

router = APIRouter(tags=["metrics"])

# Prometheus scrapes every 15s. Rebuilding the registry and re-reading both JSONL
# files on every scrape measured ~120ms per request; the body only changes when a
# worker appends a result, so a short in-process cache is enough.
CACHE_TTL_SECONDS = float(os.getenv("BACKEND_METRICS_CACHE_SECONDS", "10") or 10)
_CACHE = [0.0, b""]
_CACHE_LOCK = threading.Lock()


def _build_body() -> bytes:
    collector = MetricsCollector()
    collector.reload()
    snapshot = collector.get_snapshot()
    data = build_prometheus_metrics(snapshot)
    log_data = build_log_metrics()
    return data + b"\n" + log_data


def _cached_body() -> bytes:
    if CACHE_TTL_SECONDS <= 0:
        return _build_body()
    with _CACHE_LOCK:
        if _CACHE[1] and time.monotonic() - _CACHE[0] < CACHE_TTL_SECONDS:
            return _CACHE[1]
        body = _build_body()
        _CACHE[0] = time.monotonic()
        _CACHE[1] = body
        return body


def reset_cache() -> None:
    with _CACHE_LOCK:
        _CACHE[0] = 0.0
        _CACHE[1] = b""


@router.get("/metrics")
def get_prometheus_metrics():
    return Response(content=_cached_body(), media_type=CONTENT_TYPE_LATEST)
