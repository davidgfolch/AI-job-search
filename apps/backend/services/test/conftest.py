"""Shared fixtures for dashboard service tests."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta


def _iso(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)).isoformat()


SNAPSHOT = {
    "timestamp": "2026-09-03T10:00:00",
    "modules": {
        "aiEnrich": {
            "jobs_processed": 10,
            "jobs_succeeded": 8,
            "jobs_failed": 2,
            "pending_jobs": 3,
            "last_processed_at": _iso(),
            "last_error_at": None,
            "last_error": None,
        },
        "aiEnrichSkill": {},
    },
    "global": {},
}


def _infra(name, **over):
    entry = {
        "name": name,
        "displayName": name.title(),
        "kind": "http",
        "reachable": True,
        "url": f"http://{name}:1234",
        "detail": "/health",
        "lastActivity": None,
    }
    entry.update(over)
    return entry


_INFRASTRUCTURE = [
    _infra("ollama", kind="ollama", reachable=False, url="", detail="No Ollama server detected",
           serverUrl=None, serverIp=None, isLan=False, recentErrors=[]),
    _infra("backend"),
    _infra("web"),
    _infra("mysql", kind="database", url="mysql://mysql_db:3306", detail="Connected"),
    _infra("mongo", kind="database", url="mongodb://mongo_db:27017", detail="Connected"),
    _infra("aiformfiller"),
    _infra("cron", kind="activity", url="/logs/cron/cron.jsonl", detail="No activity logged"),
    _infra("scrapper", kind="activity", url="/logs/scrapper/scrapper.jsonl", detail="No activity logged"),
    _infra("prometheus", url="http://localhost:9090"),
    _infra("grafana", url="http://localhost:3000"),
]


def infrastructure(**ollama_over):
    """Fresh infrastructure payload, optionally overriding the ollama entry."""
    entries = deepcopy(_INFRASTRUCTURE)
    entries[0].update(ollama_over)
    return entries
