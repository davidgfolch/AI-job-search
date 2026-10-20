import json
import asyncio
from typing import Any, Dict, List
from fastapi import APIRouter, Query, Depends, Request
from fastapi.responses import StreamingResponse
from services.watcher_service import WatcherService, get_watcher_service
from services.watcher_matcher import get_watcher_matcher

router = APIRouter()


# ------------------------------------------------------------------
# SSE broadcast for watcher events
# ------------------------------------------------------------------

_watcher_event_subscribers: List[asyncio.Queue] = []
_watcher_event_lock = asyncio.Lock()


def broadcast_watcher_event(event_type: str, data: Dict[str, Any] = None) -> None:
    """Broadcast a watcher event to all SSE subscribers."""
    payload = {"type": event_type, "data": data or {}}
    message = f"data: {json.dumps(payload)}\n\n"
    for q in list(_watcher_event_subscribers):
        try:
            q.put_nowait(message)
        except Exception:
            pass


@router.get("/watcher-events")
async def watcher_events():
    """Server-Sent Events endpoint for watcher badge updates."""
    queue: asyncio.Queue = asyncio.Queue()

    async def _subscribe():
        async with _watcher_event_lock:
            _watcher_event_subscribers.append(queue)
        try:
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                message = await queue.get()
                yield message
        finally:
            async with _watcher_event_lock:
                if queue in _watcher_event_subscribers:
                    _watcher_event_subscribers.remove(queue)

    return StreamingResponse(
        _subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/watcher-stats")
def get_watcher_stats(
    request: Request,
    config_ids: str = Query(
        ..., description="Comma-separated list of filter configuration IDs"
    ),
    service: WatcherService = Depends(get_watcher_service),
):
    ids = [int(id.strip()) for id in config_ids.split(",") if id.strip()]
    cutoff_map = {}
    for config_id in ids:
        param_name = f"from_{config_id}"
        if param_name in request.query_params:
            cutoff_map[config_id] = request.query_params[param_name]
    stats = service.get_watcher_stats(config_ids=ids, cutoff_map=cutoff_map)
    return {
        str(cid): {
            "total": s["total"],
            "new_items": s["new_items"],
            "removed_items": s.get("removed_items", 0),
        }
        for cid, s in stats.items()
    }
