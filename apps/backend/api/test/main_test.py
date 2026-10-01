from fastapi.testclient import TestClient
import logging
from main import app

client = TestClient(app)

def test_uvicorn_access_log_disabled():
    assert logging.getLogger("uvicorn.access").disabled

def test_get_timezone():
    response = client.get("/api/system/timezone")
    assert response.status_code == 200
    data = response.json()
    assert "offset_minutes" in data
    assert isinstance(data["offset_minutes"], int)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_request_logging_middleware_is_wired(log_records):
    response = client.get("/health")
    assert response.status_code == 200
    records = log_records(event="http.request_completed")
    assert len(records) == 1
    assert records[0]["method"] == "GET"
    assert records[0]["path"] == "/health"
    assert records[0]["status_code"] == 200
    assert records[0]["logger"] == "backend"
    assert records[0]["module"] == "backend.middleware.request_logging"
    assert log_records(event="http.request_failed") == []


def test_request_logging_middleware_logs_error_status(log_records):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert log_records(event="http.request_completed")[0]["status_code"] == 404
    failed = log_records(event="http.request_failed")
    assert [record["level"] for record in failed] == ["warning"]
    assert failed[0]["path"] == "/api/does-not-exist"
