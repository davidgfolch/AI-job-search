import os
import urllib.request
from datetime import datetime, timezone

from commonlib.services.metrics_collector import MetricsCollector
from repositories.dashboard_repository import DashboardRepository

_repo = DashboardRepository()

MODULES = ["aienrich", "aienrichnew", "aienrichskill", "aienrich3", "aicvmatcher"]
MODULE_METRIC_KEYS = {
    "aienrich": "aiEnrich",
    "aienrichnew": "aiEnrichNew",
    "aienrichskill": "aiEnrichSkill",
    "aienrich3": "aiEnrich3",
    "aicvmatcher": "aiCvMatcher",
}
OLLAMA_MODULES = {"aienrich", "aienrichskill"}
STALE_THRESHOLD_SECONDS = 1200
OLLAMA_ERROR_WINDOW_SECONDS = 1800
OLLAMA_PROBE_TIMEOUT_SECONDS = 3
OLLAMA_CANDIDATE_URLS = ("http://ollama:11434", "http://localhost:11434")


def get_services_status() -> dict:
    collector = MetricsCollector()
    collector.reload()
    snapshot = collector.get_snapshot()
    modules = snapshot.get("modules", {})
    now = datetime.now(timezone.utc)
    services = []
    for module in MODULES:
        metric_key = MODULE_METRIC_KEYS.get(module, module)
        m = modules.get(metric_key, {})
        last_processed = m.get("last_processed_at") or _repo.read_last_activity(module)
        last_error_at = m.get("last_error_at")
        last_error = m.get("last_error")
        status = _determine_status(now, last_processed, last_error_at)
        recent_errors = _repo.read_recent_errors(module, 5)
        services.append({
            "name": module,
            "displayName": _display_name(module),
            "status": status,
            "lastActivity": last_processed,
            "usesOllama": module in OLLAMA_MODULES,
            "metrics": {
                "pendingJobs": m.get("pending_jobs", 0),
                "processed": m.get("jobs_processed", 0),
                "succeeded": m.get("jobs_succeeded", 0),
                "failed": m.get("jobs_failed", 0),
                "lastError": last_error,
                "lastErrorAt": last_error_at,
            },
            "recentErrors": recent_errors,
        })
    ollama_errors = _repo.check_ollama_errors(3, within_seconds=OLLAMA_ERROR_WINDOW_SECONDS)
    return {
        "services": services,
        "ollama": {
            "reachable": _probe_ollama(),
            "recentErrors": ollama_errors,
        },
        "timestamp": now.isoformat(),
    }


def _probe_ollama() -> bool:
    base = os.environ.get("AI_ENRICH_OLLAMA_BASE_URL")
    candidates = ([base] if base else []) + list(OLLAMA_CANDIDATE_URLS)
    for url in candidates:
        try:
            with urllib.request.urlopen(f"{url}/api/version", timeout=OLLAMA_PROBE_TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False


def _local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


def _parse_local(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return _local(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _determine_status(now: datetime, last_processed: str | None, last_error_at: str | None) -> str:
    now = _local(now)
    last_ts = _parse_local(last_processed)
    if last_ts is None:
        return "stopped"
    seconds_since = (now - last_ts).total_seconds()
    if seconds_since > STALE_THRESHOLD_SECONDS:
        return "stopped"
    error_ts = _parse_local(last_error_at)
    if error_ts is not None and error_ts >= last_ts:
        return "error"
    return "running"


def _display_name(module: str) -> str:
    names = {
        "aienrich": "AI Enrich (Ollama)",
        "aienrichnew": "AI Enrich New (HF)",
        "aienrichskill": "AI Enrich Skill",
        "aienrich3": "AI Enrich 3 (CPU)",
        "aicvmatcher": "CV Matcher",
    }
    return names.get(module, module)