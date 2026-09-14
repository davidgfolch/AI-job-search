import json
import os
from collections import deque
from datetime import datetime

LOG_SOURCES = {
    "aienrich": "/logs/aienrich/app.jsonl",
    "aienrich3": "/logs/aienrich3/app.jsonl",
    "aienrichnew": "/logs/aienrichnew/app.jsonl",
    "aienrichskill": "/logs/aienrichskill/app.jsonl",
    "aicvmatcher": "/logs/aicvmatcher/app.jsonl",
}

ERROR_LEVELS = {"error", "warning", "critical"}


class DashboardRepository:
    def read_recent_errors(self, module: str, count: int = 10) -> list[dict]:
        path = LOG_SOURCES.get(module)
        if not path or not os.path.isfile(path):
            return []
        try:
            with open(path) as f:
                lines = deque(f, count * 3)
        except OSError:
            return []
        errors = []
        for line in reversed(lines):
            if len(errors) >= count:
                break
            try:
                entry = json.loads(line)
                level = entry.get("level", "").lower()
                if level in ERROR_LEVELS:
                    errors.append({
                        "timestamp": entry.get("timestamp", ""),
                        "event": entry.get("event", ""),
                        "level": level,
                        "message": self._format_error(entry),
                    })
            except (json.JSONDecodeError, ValueError):
                continue
        return errors

    def read_last_activity(self, module: str) -> str | None:
        path = LOG_SOURCES.get(module)
        if not path or not os.path.isfile(path):
            return None
        try:
            with open(path) as f:
                lines = deque(f, 50)
        except OSError:
            return None
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                ts = entry.get("timestamp")
                if ts:
                    return ts
            except (json.JSONDecodeError, ValueError):
                continue
        return None

    def check_ollama_errors(self, count: int = 5, within_seconds: int | None = None) -> list[dict]:
        ollama_events = {"ollama.ping_failed", "ollama.unreachable", "ollama.failed", "ollama.error"}
        errors = []
        now = datetime.now()
        for module in LOG_SOURCES:
            path = LOG_SOURCES.get(module)
            if not path or not os.path.isfile(path):
                continue
            try:
                with open(path) as f:
                    lines = deque(f, 100)
            except OSError:
                continue
            for line in reversed(lines):
                if len(errors) >= count:
                    break
                try:
                    entry = json.loads(line)
                    event = entry.get("event", "")
                    if event not in ollama_events:
                        continue
                    if within_seconds is not None and not self._ts_within(entry.get("timestamp"), now, within_seconds):
                        continue
                    errors.append({
                        "timestamp": entry.get("timestamp", ""),
                        "event": event,
                        "module": module,
                        "message": self._format_error(entry),
                    })
                except (json.JSONDecodeError, ValueError):
                    continue
            if len(errors) >= count:
                break
        return errors

    @staticmethod
    def _ts_within(timestamp: str, now: datetime, within_seconds: int) -> bool:
        if not timestamp:
            return True
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return True
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return (now - dt).total_seconds() <= within_seconds

    def _format_error(self, entry: dict) -> str:
        parts = []
        if entry.get("error"):
            parts.append(str(entry["error"]))
        if entry.get("message"):
            parts.append(str(entry["message"]))
        if entry.get("base_url"):
            parts.append(f"url={entry['base_url']}")
        if entry.get("module"):
            parts.append(f"module={entry['module']}")
        if entry.get("job_id"):
            parts.append(f"job={entry['job_id']}")
        return " | ".join(parts) if parts else entry.get("event", "unknown error")
