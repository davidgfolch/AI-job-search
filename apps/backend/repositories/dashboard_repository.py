import json
import os
from collections import deque
from datetime import datetime

from commonlib.log_writer import resolve_read_path
from commonlib.observability import get_logger

logger = get_logger("backend.repositories.dashboard_repository")

LOG_SOURCES = {
    "aienrich": "/logs/aienrich/aiEnrich.jsonl",
    "aienrich3": "/logs/aienrich3/aiEnrich3.jsonl",
    "aienrichnew": "/logs/aienrichnew/aiEnrichNew.jsonl",
    "aienrichskill": "/logs/aienrichskill/aiEnrichSkill.jsonl",
    "aicvmatcher": "/logs/aicvmatcher/aiCvMatcher.jsonl",
}

ERROR_LEVELS = {"error", "warning", "critical"}


def resolve_log_path(module: str) -> str | None:
    path = LOG_SOURCES.get(module)
    return resolve_read_path(path) if path else None


class DashboardRepository:
    def read_recent_errors(self, module: str, count: int = 10) -> list[dict]:
        path = resolve_log_path(module)
        if not path:
            return []
        try:
            with open(path) as f:
                lines = deque(f, count * 3)
        except OSError as e:
            logger.debug("logs.read_failed", error=str(e), source_module=module, source="recent_errors")
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
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug("logs.line_skipped", error=str(e), source_module=module, source="recent_errors")
                continue
        return errors

    def read_last_activity(self, module: str) -> str | None:
        path = resolve_log_path(module)
        if not path:
            return None
        try:
            with open(path) as f:
                lines = deque(f, 50)
        except OSError as e:
            logger.debug("logs.read_failed", error=str(e), source_module=module, source="last_activity")
            return None
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                ts = entry.get("timestamp")
                if ts:
                    return ts
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug("logs.line_skipped", error=str(e), source_module=module, source="last_activity")
                continue
        return None

    def check_ollama_errors(self, count: int = 5, within_seconds: int | None = None) -> list[dict]:
        ollama_events = {"ollama.ping_failed", "ollama.unreachable", "ollama.failed", "ollama.error"}
        errors = []
        now = datetime.now()
        for module in LOG_SOURCES:
            path = resolve_log_path(module)
            if not path:
                continue
            try:
                with open(path) as f:
                    lines = deque(f, 100)
            except OSError as e:
                logger.debug("logs.read_failed", error=str(e), source_module=module, source="ollama_errors")
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
                except (json.JSONDecodeError, ValueError) as e:
                    logger.debug("logs.line_skipped", error=str(e), source_module=module, source="ollama_errors")
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
        except ValueError as e:
            logger.debug("logs.timestamp_unparsed", error=str(e))
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
