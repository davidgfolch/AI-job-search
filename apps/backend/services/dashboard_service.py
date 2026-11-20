from datetime import datetime, timezone

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.systemUtil import isDocker
from repositories.dashboard_repository import DashboardRepository

from .dashboard_health import get_infrastructure_status
from .dashboard_utils import (
    _determine_status, _display_name, _pick_freshest,
)

logger = get_logger("backend.services.dashboard_service")

_repo = DashboardRepository()

MODULES = ["aienrich", "aienrichskill", "aicvmatcher"]
MODULE_METRIC_KEYS = {
    "aienrich": "aiEnrich",
    "aienrichskill": "aiEnrichSkill",
    "aicvmatcher": "aiCvMatcher",
}
OLLAMA_MODULES = {"aienrich", "aienrichskill"}
LLM_BACKEND = getEnv("AI_ENRICH_LLM_BACKEND", "ollama").strip().lower()


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
        last_processed = _pick_freshest(m.get("last_processed_at"), m.get("last_heartbeat_at"), _repo.read_last_activity(module))
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
            "deployment": m.get("deployment") or ("docker" if isDocker() else "host"),
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
    infrastructure = get_infrastructure_status(_repo)
    by_name = {entry["name"]: entry for entry in infrastructure}
    ollama = by_name["ollama"]
    return {
        "services": services,
        "infrastructure": infrastructure,
        "ollama": {
            "reachable": ollama["reachable"],
            "serverUrl": ollama.get("serverUrl"),
            "serverIp": ollama.get("serverIp"),
            "isLan": ollama.get("isLan", False),
            "recentErrors": ollama.get("recentErrors", []),
        },
        "llmBackend": LLM_BACKEND,
        "prometheus": _health_alias(by_name["prometheus"]),
        "grafana": _health_alias(by_name["grafana"]),
        "timestamp": now.isoformat(),
        "deployment": "docker" if isDocker() else "host",
    }


def _health_alias(entry: dict) -> dict:
    """Keep the pre-unification health fields stable for API consumers."""
    return {"reachable": entry["reachable"], "url": entry["url"]}
