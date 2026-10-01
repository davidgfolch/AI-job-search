import asyncio

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from middleware import request_logging
from middleware.request_logging import RequestLoggingMiddleware

SUCCESS_STATUSES = [200, 201, 204, 302, 399]
FAILURE_STATUSES = [400, 404, 422, 500, 502]
QUERY_STRING = b"search=secret-token"


def _asgi_app(status=200, chunks=((b"payload", False),), error=None):
    async def app(scope, receive, send):
        if error is not None:
            raise error
        await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"text/plain")]})
        for body, more_body in chunks:
            await send({"type": "http.response.body", "body": body, "more_body": more_body})
    return app


def _call(app, scope=None):
    sent = []
    scope = scope if scope is not None else {"type": "http", "method": "GET", "path": "/api/jobs", "query_string": QUERY_STRING}
    middleware = RequestLoggingMiddleware(app)

    async def send(message):
        sent.append(message)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    asyncio.run(middleware(scope, receive, send))
    return sent


def _client_app():
    app = FastAPI()

    @app.get("/ok")
    def ok():
        return {"status": "ok"}

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    @app.get("/unavailable")
    def unavailable():
        raise HTTPException(status_code=503, detail="down")

    @app.get("/stream")
    def stream():
        return StreamingResponse(iter([b"one", b"two"]), media_type="text/plain")

    app.add_middleware(RequestLoggingMiddleware)
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("status", SUCCESS_STATUSES, ids=lambda s: str(s))
def test_success_status_logs_one_completed_record(log_records, status):
    _call(_asgi_app(status=status))
    records = log_records(event="http.request_completed")
    assert len(records) == 1
    assert records[0]["level"] == "info"
    assert records[0]["method"] == "GET"
    assert records[0]["path"] == "/api/jobs"
    assert records[0]["status_code"] == status
    assert records[0]["duration_ms"] >= 0
    assert records[0]["logger"] == "backend"
    assert records[0]["module"] == "backend.middleware.request_logging"
    assert log_records(event="http.request_failed") == []


@pytest.mark.parametrize("status", FAILURE_STATUSES, ids=lambda s: str(s))
def test_error_status_adds_warning_record(log_records, status):
    _call(_asgi_app(status=status))
    completed = log_records(event="http.request_completed")
    failed = log_records(event="http.request_failed")
    assert [record["level"] for record in completed] == ["info"]
    assert [record["level"] for record in failed] == ["warning"]
    assert completed[0]["status_code"] == status
    assert failed[0]["status_code"] == status
    assert failed[0]["method"] == "GET"
    assert failed[0]["path"] == "/api/jobs"


@pytest.mark.parametrize("method,path", [("GET", "/health"), ("POST", "/api/salary/calculate"), ("DELETE", "/api/jobs/7")])
def test_method_and_path_are_recorded(log_records, method, path):
    _call(_asgi_app(), scope={"type": "http", "method": method, "path": path, "query_string": b""})
    record = log_records(event="http.request_completed")[0]
    assert record["method"] == method
    assert record["path"] == path


def test_query_string_and_body_are_never_logged(log_records):
    _call(_asgi_app(chunks=((b"secret-body", False),)))
    raw = log_records.path.read_text(encoding="utf-8")
    assert "secret-token" not in raw
    assert "secret-body" not in raw
    assert "?" not in log_records(event="http.request_completed")[0]["path"]


def test_streaming_chunks_are_forwarded_untouched(log_records):
    chunks = ((b"one", True), (b"two", True), (b"three", False))
    sent = _call(_asgi_app(status=200, chunks=chunks))
    assert sent[0]["type"] == "http.response.start"
    assert [message["body"] for message in sent[1:]] == [b"one", b"two", b"three"]
    assert [message["more_body"] for message in sent[1:]] == [True, True, False]
    assert len(log_records(event="http.request_completed")) == 1


def test_unhandled_exception_is_logged_and_repropagated(log_records):
    middleware = RequestLoggingMiddleware(_asgi_app(error=RuntimeError("boom")))

    async def send(message):
        return None

    async def receive():
        return {"type": "http.request"}

    scope = {"type": "http", "method": "POST", "path": "/api/jobs", "query_string": b""}
    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(middleware(scope, receive, send))
    failed = log_records(event="http.request_failed")
    assert len(failed) == 1
    assert failed[0]["level"] == "error"
    assert failed[0]["error"] == "boom"
    assert failed[0]["status_code"] == 500
    assert "RuntimeError" in failed[0]["exception"]
    assert log_records(event="http.request_completed") == []


def test_non_http_scope_is_forwarded_without_logging(log_records):
    seen = {}

    async def app(scope, receive, send):
        seen["scope"] = scope
        await send({"type": "websocket.accept"})

    scope = {"type": "websocket", "path": "/ws"}
    sent = _call(app, scope=scope)
    assert seen["scope"] is scope
    assert sent == [{"type": "websocket.accept"}]
    assert log_records() == []


def test_middleware_never_raises_when_the_logger_fails(monkeypatch):
    class _ExplodingLogger:
        def __getattr__(self, _name):
            def _boom(*args, **kwargs):
                raise OSError("stdout closed")
            return _boom

    monkeypatch.setattr(request_logging, "logger", _ExplodingLogger())
    sent = _call(_asgi_app(status=500, chunks=((b"still-here", False),)))
    assert [message["body"] for message in sent[1:]] == [b"still-here"]


def test_wired_into_an_app_success(log_records):
    response = _client_app().get("/ok")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    record = log_records(event="http.request_completed")[0]
    assert record["path"] == "/ok"
    assert record["status_code"] == 200


def test_wired_into_an_app_server_error(log_records):
    response = _client_app().get("/boom")
    assert response.status_code == 500
    failed = log_records(event="http.request_failed")
    assert [record["level"] for record in failed] == ["error"]
    assert failed[0]["status_code"] == 500
    assert log_records(event="http.request_completed") == []


def test_wired_into_an_app_error_status_logs_warning(log_records):
    response = _client_app().get("/unavailable")
    assert response.status_code == 503
    assert log_records(event="http.request_completed")[0]["status_code"] == 503
    assert [record["level"] for record in log_records(event="http.request_failed")] == ["warning"]


def test_wired_into_an_app_streaming(log_records):
    response = _client_app().get("/stream")
    assert response.status_code == 200
    assert response.content == b"onetwo"
    assert len(log_records(event="http.request_completed")) == 1
