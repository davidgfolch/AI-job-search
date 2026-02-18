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
