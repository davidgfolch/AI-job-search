import json
import os
from collections import deque
from datetime import datetime

from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

LOG_SOURCES = {
    "aiEnrich": "/logs/aienrich/app.jsonl",
    "aiEnrich3": "/logs/aienrich3/app.jsonl",
    "aiEnrichNew": "/logs/aienrichnew/app.jsonl",
}
MAX_LOG_ENTRIES = 50


def build_prometheus_metrics(snapshot: dict) -> bytes:
    registry = CollectorRegistry()
    modules = snapshot.get("modules", {})
    if not modules:
        return b""

    jobs_total = Gauge("ai_enrich_jobs_processed_total", "Total jobs processed", ["module"], registry=registry)
    jobs_ok = Gauge("ai_enrich_jobs_succeeded_total", "Total jobs succeeded", ["module"], registry=registry)
    jobs_fail = Gauge("ai_enrich_jobs_failed_total", "Total jobs failed", ["module"], registry=registry)
    dur_total = Gauge("ai_enrich_duration_seconds_total", "Sum of all job durations", ["module"], registry=registry)
    dur_p50 = Gauge("ai_enrich_duration_seconds_p50", "Duration p50 percentile", ["module"], registry=registry)
    dur_p90 = Gauge("ai_enrich_duration_seconds_p90", "Duration p90 percentile", ["module"], registry=registry)
    dur_p99 = Gauge("ai_enrich_duration_seconds_p99", "Duration p99 percentile", ["module"], registry=registry)
    dur_avg = Gauge("ai_enrich_duration_seconds_avg", "Duration avg", ["module"], registry=registry)
    cache_hits = Gauge("ai_enrich_cache_hits_total", "Total cache hits", ["module"], registry=registry)
    cache_misses = Gauge("ai_enrich_cache_misses_total", "Total cache misses", ["module"], registry=registry)
    pending = Gauge("ai_enrich_pending_jobs", "Currently pending jobs", ["module"], registry=registry)
    last_ts = Gauge("ai_enrich_last_processed_timestamp", "Last job processed timestamp", ["module"], registry=registry)
    g_total_jobs = Gauge("ai_enrich_total_jobs", "Total jobs across all modules", registry=registry)
    g_total_err = Gauge("ai_enrich_total_errors", "Total errors across all modules", registry=registry)
    g_modules = Gauge("ai_enrich_modules_count", "Number of modules reporting", registry=registry)

    for name, data in modules.items():
        jobs_total.labels(module=name).set(data.get("jobs_processed", 0))
        jobs_ok.labels(module=name).set(data.get("jobs_succeeded", 0))
        jobs_fail.labels(module=name).set(data.get("jobs_failed", 0))
        dur_total.labels(module=name).set(data.get("total_duration", 0))
        if "p50" in data:
            dur_p50.labels(module=name).set(data["p50"])
        if "p90" in data:
            dur_p90.labels(module=name).set(data["p90"])
        if "p99" in data:
            dur_p99.labels(module=name).set(data["p99"])
        if "avg" in data:
            dur_avg.labels(module=name).set(data["avg"])
        cache_hits.labels(module=name).set(data.get("cache_hits", 0))
        cache_misses.labels(module=name).set(data.get("cache_misses", 0))
        pending.labels(module=name).set(data.get("pending_jobs", 0))
        last_processed = data.get("last_processed_at")
        if last_processed:
            try:
                ts = datetime.fromisoformat(last_processed).timestamp()
                last_ts.labels(module=name).set(ts)
            except ValueError:
                pass

    total_global = snapshot.get("global", {})
    g_total_jobs.set(total_global.get("total_jobs", 0))
    g_total_err.set(total_global.get("total_errors", 0))
    g_modules.set(len(modules))

    return generate_latest(registry)


def build_log_metrics() -> bytes:
    registry = CollectorRegistry()
    gauge = Gauge(
        "ai_enrich_job_duration_seconds",
        "Per-job enrichment duration in seconds, sourced from JSONL log files",
        ["module", "job_id"],
        registry=registry,
    )

    for module, path in LOG_SOURCES.items():
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as f:
                lines = deque(f, MAX_LOG_ENTRIES * 2)
        except OSError:
            continue
        count = 0
        for line in reversed(lines):
            if count >= MAX_LOG_ENTRIES:
                break
            try:
                entry = json.loads(line)
                if entry.get("event") == "job.result" and "duration" in entry:
                    gauge.labels(module=module, job_id=str(entry["job_id"])).set(float(entry["duration"]))
                    count += 1
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

    return generate_latest(registry)
