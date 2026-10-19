"""Shared fixtures for dashboard service tests."""
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
        "aiEnrichNew": {},
    },
    "global": {},
}
