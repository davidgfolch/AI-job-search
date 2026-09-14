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
STALE_THRESHOLD_SECONDS = 300


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
        last_processed = m.get("last_processed_at")
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
    ollama_errors = _repo.check_ollama_errors(3)
    ollama_reachable = len(ollama_errors) == 0
    return {
        "services": services,
        "ollama": {
            "reachable": ollama_reachable,
            "recentErrors": ollama_errors,
        },
        "timestamp": now.isoformat(),
    }


def _determine_status(now: datetime, last_processed: str | None, last_error_at: str | None) -> str:
    if not last_processed:
        return "stopped"
    try:
        last_ts = datetime.fromisoformat(last_processed).replace(tzinfo=timezone.utc)
    except ValueError:
        return "stopped"
    seconds_since = (now - last_ts).total_seconds()
    if seconds_since > STALE_THRESHOLD_SECONDS:
        return "stopped"
    if last_error_at:
        try:
            err_ts = datetime.fromisoformat(last_error_at).replace(tzinfo=timezone.utc)
            if err_ts >= last_ts:
                return "error"
        except ValueError:
            pass
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
