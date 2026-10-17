"""Per-request structured logging for the backend API.

Raw ASGI middleware: it reads only `http.response.start` off the send channel and never
touches a body chunk, so streaming and SSE responses pass through untouched and no
payload can reach the log. Only `method`, the `path` without its query string, the
`status_code` and the `duration_ms` are recorded - never headers, cookies, query
strings, request or response bodies.

Every request produces one `http.request_completed` record. A status outside 200-399
adds a `http.request_failed` warning, and an unhandled exception produces a single
`http.request_failed` error record before the exception keeps propagating untouched -
so a 500 raised by Starlette's outer `ServerErrorMiddleware` is recorded as the error
it is, without a duplicate completed record.

`module` is stamped from the caller, so these records read as this module rather than as
whichever shared helper they passed through. The `get_logger()` name below is only a
fallback for records with no app frame above them.
"""
import time
from contextlib import suppress

from commonlib.observability import get_logger

logger = get_logger("backend.middleware.request_logging")

FIRST_SUCCESS_STATUS = 200
LAST_SUCCESS_STATUS = 399
UNKNOWN_STATUS = 500


def _fields(method: str, path: str, status: int, started: float) -> dict:
    return {"method": method, "path": path, "status_code": status, "duration_ms": round((time.perf_counter() - started) * 1000, 3)}


class _StatusCapture:
    """ASGI `send` proxy that remembers the response status code."""

    def __init__(self, send):
        self._send = send
        self.status = 0

    async def __call__(self, message):
        if message.get("type") == "http.response.start":
            self.status = message.get("status", 0)
        await self._send(message)


class RequestLoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "")
        path = scope.get("path", "")
        started = time.perf_counter()
        capture = _StatusCapture(send)
        try:
            await self.app(scope, receive, capture)
        except Exception as e:
            fields = _fields(method, path, capture.status or UNKNOWN_STATUS, started)
            with suppress(Exception):
                logger.exception("http.request_failed", error=str(e), **fields)
            raise
        fields = _fields(method, path, capture.status or UNKNOWN_STATUS, started)
        with suppress(Exception):
            logger.info("http.request_completed", **fields)
        if not FIRST_SUCCESS_STATUS <= fields["status_code"] <= LAST_SUCCESS_STATUS:
            with suppress(Exception):
                logger.warning("http.request_failed", **fields)
