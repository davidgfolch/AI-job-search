from datetime import datetime, timezone

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.systemUtil import isDocker
from repositories.dashboard_repository import DashboardRepository

from .dashboard_probe import _probe_ollama
from .dashboard_utils import (
    _determine_status, _display_name, _pick_freshest,
)

logger = get_logger("backend.services.dashboard_service")

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
OLLAMA_ERROR_WINDOW_SECONDS = 1800
PROMETHEUS_URL = getEnv("PROMETHEUS_URL", "http://host.docker.internal:9090").strip().rstrip("/")
GRAFANA_URL = getEnv("GRAFANA_URL", "http://host.docker.internal:3000").strip().rstrip("/")


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
    ollama_errors = _repo.check_ollama_errors(3, within_seconds=OLLAMA_ERROR_WINDOW_SECONDS)
    ollama_info = _probe_ollama()
    return {
        "services": services,
        "ollama": {
            **ollama_info,
            "recentErrors": ollama_errors,
        },
        "prometheus": _probe_service(PROMETHEUS_URL, "/-/healthy"),
        "grafana": _probe_service(GRAFANA_URL, "/api/health"),
        "timestamp": now.isoformat(),
        "deployment": "docker" if isDocker() else "host",
    }


def _probe_service(base_url: str, health_path: str) -> dict:
    """Probe a service health endpoint; returns {reachable, url}."""
    try:
        import urllib.request
        with urllib.request.urlopen(f"{base_url.rstrip('/')}{health_path}", timeout=3) as resp:
            return {"reachable": resp.status == 200, "url": base_url}
    except Exception as e:
        logger.debug("service.probe_failed", error=str(e), url=base_url)
        return {"reachable": False, "url": base_url}
