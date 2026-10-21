from typing import Iterable

import requests

from commonlib.observability import get_logger

logger = get_logger("commonlib.watcher_notify")

NOTIFY_PATH = "/api/jobs/notify-watcher"


def notify_watcher(
    job_ids: Iterable[int],
    base_url: str,
    event_type: str = "jobs_enriched",
    timeout: float = 5,
) -> bool:
    """Tell the backend to enqueue job ids for watcher matching and SSE broadcast.

    Called by enrichment workers after persisting a job. Best-effort by design: the
    job is already saved, so a failed notification is logged and reported through
    the return value instead of raised. Returns True when the backend accepted it.
    """
    ids = list(job_ids)
    if not ids:
        return True
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}{NOTIFY_PATH}",
            json={"ids": ids, "event_type": event_type},
            timeout=timeout,
        )
    except Exception as ex:
        logger.warning("watcher.notify_failed", job_ids=ids, error=str(ex))
        return False
    if not response.ok:
        logger.warning(
            "watcher.notify_rejected",
            job_ids=ids,
            status_code=response.status_code,
            base_url=base_url,
        )
    return response.ok
