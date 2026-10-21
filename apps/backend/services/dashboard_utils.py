from datetime import datetime, timezone

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger

logger = get_logger("backend.services.dashboard_utils")

STALE_THRESHOLD_SECONDS = 1200
BACKEND_LABELS = {
    "ollama": "Ollama",
    "ollama_cloud": "Ollama Cloud",
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
}


def _local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


def _parse_local(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return _local(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError as e:
        logger.debug("metrics.timestamp_unparsed", error=str(e))
        return None


def _pick_freshest(*candidates: str | None) -> str | None:
    best, best_ts = None, None
    for candidate in candidates:
        if not candidate:
            continue
        ts = _parse_local(candidate)
        if ts is not None and (best_ts is None or ts > best_ts):
            best, best_ts = candidate, ts
    return best


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
        "aienrichskill": "AI Enrich Skill",
        "aicvmatcher": "CV Matcher",
    }
    return names.get(module, module)
