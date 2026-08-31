import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.statistics_archived import router
from services.statistics_archived_service import StatisticsArchivedService
from fastapi import FastAPI


@pytest.fixture
def mock_service():
    return MagicMock(spec=StatisticsArchivedService)


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


def test_get_archived_history_stats(app, mock_service):
    mock_service.get_archived_history_stats.return_value = [
        {"dateCreated": "2023-01-01", "applied": 1, "discarded": 0, "interview": 0}
    ]

    with patch("api.statistics_archived.service", mock_service):
        client = TestClient(app)
        response = client.get("/history")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_snapshots_by_reason(app, mock_service):
    mock_service.get_snapshots_by_reason.return_value = [
        {"snapshot_reason": "DELETED", "count": 10}
    ]

    with patch("api.statistics_archived.service", mock_service):
        client = TestClient(app)
        response = client.get("/snapshots-by-reason")

    assert response.status_code == 200
    assert response.json()[0]["count"] == 10


@pytest.mark.parametrize("path,method", [
    ("/sources-date", "get_archived_sources_by_date"),
    ("/sources-hour", "get_archived_sources_by_hour"),
    ("/sources-weekday", "get_archived_sources_by_weekday"),
    ("/combined/history", "get_combined_history_stats"),
    ("/combined/sources-date", "get_combined_sources_by_date"),
    ("/combined/sources-hour", "get_combined_sources_by_hour"),
    ("/combined/sources-weekday", "get_combined_sources_by_weekday"),
    ("/snapshots-by-platform", "get_snapshots_by_platform"),
], ids=["sources-date", "sources-hour", "sources-weekday", "combined-history",
        "combined-sources-date", "combined-sources-hour", "combined-sources-weekday",
        "snapshots-by-platform"])
def test_archived_endpoints(app, mock_service, path, method):
    method_mock = getattr(mock_service, method)
    method_mock.return_value = [{"dateCreated": "2023-01-01", "total": 1}]

    with patch("api.statistics_archived.service", mock_service):
        client = TestClient(app)
        response = client.get(path)

    assert response.status_code == 200
    assert len(response.json()) == 1
    method_mock.assert_called_once()
