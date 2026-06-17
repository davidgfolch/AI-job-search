import json
import os
import time
import threading
from collections import defaultdict

from commonlib.environmentUtil import getEnv

METRICS_FILE = getEnv(
    "AI_ENRICH_METRICS_FILE",
    os.path.join("data", "metrics", "enrichment_metrics.json"),
)

ROLLING_WINDOW = 1000


class MetricsCollector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._modules: dict[str, dict] = defaultdict(
            lambda: {
                "jobs_processed": 0,
                "jobs_succeeded": 0,
                "jobs_failed": 0,
                "total_duration": 0.0,
                "durations": [],
                "cache_hits": 0,
                "cache_misses": 0,
                "last_processed_at": None,
                "last_error_at": None,
                "last_error": None,
                "pending_jobs": 0,
            }
        )
        self._load()

    def record_job(self, module: str, duration: float, success: bool):
        with self._lock:
            m = self._modules[module]
            m["jobs_processed"] += 1
            m["total_duration"] += duration
            m["durations"].append(duration)
            if len(m["durations"]) > ROLLING_WINDOW:
                m["durations"].pop(0)
            if success:
                m["jobs_succeeded"] += 1
            else:
                m["jobs_failed"] += 1
            m["last_processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    def record_error(self, module: str, error: str):
        with self._lock:
            m = self._modules[module]
            m["last_error_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            m["last_error"] = error[:200]

    def set_pending(self, module: str, count: int):
        with self._lock:
            self._modules[module]["pending_jobs"] = count

    def get_snapshot(self) -> dict:
        with self._lock:
            result = {}
            for name, m in self._modules.items():
                d = dict(m)
                durations = d.pop("durations")
                if durations:
                    sorted_d = sorted(durations)
                    n = len(sorted_d)
                    d["p50"] = sorted_d[n // 2]
                    d["p90"] = sorted_d[int(n * 0.9)]
                    d["p99"] = sorted_d[int(n * 0.99)]
                    d["avg"] = sum(sorted_d) / n
                result[name] = d
            return {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "modules": result,
                "global": {
                    "total_jobs": sum(
                        m["jobs_processed"] for m in self._modules.values()
                    ),
                    "total_errors": sum(
                        m["jobs_failed"] for m in self._modules.values()
                    ),
                },
            }

    def persist(self):
        os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
        raw = {"modules": {name: dict(m) for name, m in self._modules.items()}}
        with open(METRICS_FILE, "w") as f:
            json.dump(raw, f, indent=2, default=str)

    def reload(self):
        with self._lock:
            self._modules.clear()
            self._load()

    def _load(self):
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE) as f:
                    data = json.load(f)
                    for name, mdata in data.get("modules", {}).items():
                        m = self._modules[name]
                        for k, v in mdata.items():
                            if k not in ("p50", "p90", "p99", "avg"):
                                m[k] = v
                        if not m.get("durations"):
                            for k in ("p50", "p90", "p99", "avg"):
                                if k in mdata:
                                    m[k] = mdata[k]
            except (json.JSONDecodeError, IOError):
                pass
