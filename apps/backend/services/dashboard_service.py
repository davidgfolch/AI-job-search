import socket
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlsplit

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from commonlib.ollama_probe import get_last_ollama_server, resolve_ollama_url
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.systemUtil import isDocker
from repositories.dashboard_repository import DashboardRepository

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
STALE_THRESHOLD_SECONDS = 1200
OLLAMA_ERROR_WINDOW_SECONDS = 1800
OLLAMA_PROBE_TIMEOUT_SECONDS = 3
LOCAL_HOSTS = {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}
PROMETHEUS_URL = getEnv("PROMETHEUS_URL", "http://host.docker.internal:9090").strip().rstrip("/")
GRAFANA_URL = getEnv("GRAFANA_URL", "http://host.docker.internal:3000").strip().rstrip("/")
BACKEND_LABELS = {
    "ollama": "Ollama",
    "ollama_cloud": "Ollama Cloud",
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
}


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


def _host_ip(url: str) -> str | None:
    host = urlsplit(url).hostname or ""
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


def _is_lan_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    if host in LOCAL_HOSTS:
        return False
    ip = _host_ip(url)
    return bool(ip) and not ip.startswith("127.")


def _ollama_info(url: str | None) -> dict:
    """Build the ollama info dict for a given URL (None => unreachable)."""
    if url is None:
        last = get_last_ollama_server()
        return {
            "reachable": False,
            "serverUrl": last.get("url"),
            "serverIp": last.get("ip"),
            "isLan": bool(last.get("is_lan")),
        }
    return {
        "reachable": True,
        "serverUrl": url,
        "serverIp": _host_ip(url),
        "isLan": _is_lan_url(url),
    }


def _probe_ollama() -> dict:
    """Return Ollama server info, probing the last-known server first (no cache).

    The last-known server IP:port is probed with a fresh request every time, so
    a server that came back up is detected immediately instead of waiting out a
    TTL. If it no longer answers, the configured candidates and LAN scan are
    tried as fallbacks, and any newly found server becomes the new last-known.
    The last-known server address is always reported (even when unreachable) so
    the dashboard keeps showing the previously detected server instead of going
    blank."""
    last = get_last_ollama_server()
    last_url = last.get("url")

    # 1. Probe the last-known server directly, fresh, no cache.
    if last_url:
        try:
            with urllib.request.urlopen(f"{last_url.rstrip('/')}/api/version", timeout=OLLAMA_PROBE_TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    return _ollama_info(last_url)
        except Exception as e:
            logger.debug("ollama.last_known_probe_failed", error=str(e), url=last_url)

    # 2. Last-known is down: try configured candidates + LAN scan.
    resolved = resolve_ollama_url(timeout=OLLAMA_PROBE_TIMEOUT_SECONDS, log=logger)
    if resolved is not None:
        return _ollama_info(resolved)

    # 3. Nothing reachable: report the last-known address as unreachable.
    return _ollama_info(None)


def _probe_service(base_url: str, health_path: str) -> dict:
    """Probe a service health endpoint; returns {reachable, url}."""
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}{health_path}", timeout=OLLAMA_PROBE_TIMEOUT_SECONDS) as resp:
            return {"reachable": resp.status == 200, "url": base_url}
    except Exception as e:
        logger.debug("service.probe_failed", error=str(e), url=base_url)
        return {"reachable": False, "url": base_url}


def _local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


def _pick_freshest(*candidates: str | None) -> str | None:
    best, best_ts = None, None
    for candidate in candidates:
        if not candidate:
            continue
        ts = _parse_local(candidate)
        if ts is not None and (best_ts is None or ts > best_ts):
            best, best_ts = candidate, ts
    return best


def _parse_local(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return _local(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError as e:
        logger.debug("metrics.timestamp_unparsed", error=str(e))
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
    if module == "aienrich":
        backend = getEnv("AI_ENRICH_BACKEND", "ollama").strip().lower()
        label = BACKEND_LABELS.get(backend) or backend.replace("_", " ").title() or "Ollama"
        return f"AI Enrich ({label})"
    names = {
        "aienrichnew": "AI Enrich New (HF)",
        "aienrichskill": "AI Enrich Skill",
        "aienrich3": "AI Enrich 3 (CPU)",
        "aicvmatcher": "CV Matcher",
    }
    return names.get(module, module)