from datetime import datetime

from commonlib.environmentUtil import getEnv
from commonlib.mongo_config import resolve_mongo_uri
from commonlib.systemUtil import isDocker
from repositories.dashboard_probe_repository import DashboardProbeRepository
from repositories.dashboard_repository import DashboardRepository

from .dashboard_probe import _probe_ollama, _probe_service
from .dashboard_utils import _parse_local

_IN_DOCKER = isDocker()
PROMETHEUS_URL = getEnv("PROMETHEUS_URL", "http://host.docker.internal:9090").strip().rstrip("/")
GRAFANA_URL = getEnv("GRAFANA_URL", "http://host.docker.internal:3000").strip().rstrip("/")
BACKEND_URL = getEnv("DASHBOARD_BACKEND_URL", "http://backend:8000" if _IN_DOCKER else "http://localhost:8000").strip().rstrip("/")
WEB_URL = getEnv("DASHBOARD_WEB_URL", "http://web:5173" if _IN_DOCKER else "http://localhost:5173").strip().rstrip("/")
FORM_FILLER_URL = getEnv("DASHBOARD_FORM_FILLER_URL", "http://aiformfiller:8080" if _IN_DOCKER else "http://localhost:8080").strip().rstrip("/")
OLLAMA_ERROR_WINDOW_SECONDS = 1800
ACTIVITY_WINDOW_SECONDS = int(getEnv("DASHBOARD_ACTIVITY_WINDOW_SECONDS", "86400"))


def get_infrastructure_status(repo: DashboardRepository) -> list[dict]:
    """Return every non-worker service the dashboard reports, in display order."""
    db_repo = DashboardProbeRepository()
    mongo_uri = resolve_mongo_uri()
    mysql_ok, mysql_detail = db_repo.probe_mysql()
    mongo_ok, mongo_detail = db_repo.probe_mongo(mongo_uri)
    return [
        _ollama_entry(repo),
        _http_entry("backend", "Backend", BACKEND_URL, "/health"),
        _http_entry("web", "Web", WEB_URL, "/"),
        _database_entry("mysql", "MySQL", db_repo.display_url("mysql", ""), mysql_ok, mysql_detail),
        _database_entry("mongo", "MongoDB", db_repo.display_url("mongo", mongo_uri), mongo_ok, mongo_detail),
        _http_entry("aiformfiller", "AI Form Filler", FORM_FILLER_URL, "/api/health"),
        _activity_entry("cron", "Cron", "/logs/cron/cron.jsonl", repo),
        _activity_entry("scrapper", "Scrapper", "/logs/scrapper/scrapper.jsonl", repo),
        _http_entry("prometheus", "Prometheus", PROMETHEUS_URL, "/-/healthy"),
        _http_entry("grafana", "Grafana", GRAFANA_URL, "/api/health"),
    ]


def _ollama_entry(repo: DashboardRepository) -> dict:
    info = _probe_ollama()
    return {
        "name": "ollama",
        "displayName": "Ollama",
        "kind": "ollama",
        "reachable": info["reachable"],
        "url": info.get("serverUrl") or "",
        "detail": "Ollama server" if info["reachable"] else "No Ollama server detected",
        "lastActivity": None,
        "serverUrl": info.get("serverUrl"),
        "serverIp": info.get("serverIp"),
        "isLan": info.get("isLan", False),
        "recentErrors": repo.check_ollama_errors(3, within_seconds=OLLAMA_ERROR_WINDOW_SECONDS),
    }


def _http_entry(name: str, display_name: str, url: str, path: str) -> dict:
    result = _probe_service(url, path)
    return {
        "name": name,
        "displayName": display_name,
        "kind": "http",
        "reachable": result["reachable"],
        "url": result["url"],
        "detail": path,
        "lastActivity": None,
    }


def _database_entry(name: str, display_name: str, url: str, ok: bool, detail: str) -> dict:
    return {
        "name": name,
        "displayName": display_name,
        "kind": "database",
        "reachable": ok,
        "url": url,
        "detail": "Connected" if ok else detail,
        "lastActivity": None,
    }


def _activity_entry(module: str, display_name: str, log_path: str, repo: DashboardRepository) -> dict:
    last = repo.read_last_activity(module)
    parsed = _parse_local(last)
    recent = parsed is not None and (datetime.now() - parsed).total_seconds() <= ACTIVITY_WINDOW_SECONDS
    return {
        "name": module,
        "displayName": display_name,
        "kind": "activity",
        "reachable": recent,
        "url": log_path,
        "detail": "Last activity" if recent else ("No recent activity" if last else "No activity logged"),
        "lastActivity": last,
    }
