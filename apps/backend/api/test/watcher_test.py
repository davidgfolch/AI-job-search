import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_watcher_service(client):
    from api.watcher import get_watcher_service
    mock_watcher = MagicMock()
    client.app.dependency_overrides[get_watcher_service] = lambda: mock_watcher
    yield mock_watcher
    client.app.dependency_overrides.pop(get_watcher_service, None)


@pytest.mark.parametrize("query_params, expected_ids, expected_cutoff", [
    ("config_ids=1,3&from_1=2023-01-01T00:00:00", [1, 3], {1: "2023-01-01T00:00:00"}),
    ("config_ids=2", [2], {}),
], ids=["with_cutoff", "without_cutoff"])
def test_watcher_stats(client, mock_watcher_service, query_params, expected_ids, expected_cutoff):
    mock_watcher_service.get_watcher_stats.return_value = {}
    response = client.get(f"/api/jobs/watcher-stats?{query_params}")
    assert response.status_code == 200
    mock_watcher_service.get_watcher_stats.assert_called_once()
    call_kwargs = mock_watcher_service.get_watcher_stats.call_args[1]
    assert call_kwargs["config_ids"] == expected_ids
    assert call_kwargs["cutoff_map"] == expected_cutoff


def test_watcher_stats_returns_stats(client, mock_watcher_service):
    mock_watcher_service.get_watcher_stats.return_value = {
        1: {"total": 5, "new_items": 2, "removed_items": 1},
        2: {"total": 3, "new_items": 0, "removed_items": 0},
    }
    response = client.get("/api/jobs/watcher-stats?config_ids=1,2")
    assert response.status_code == 200
    data = response.json()
    assert data["1"]["total"] == 5
    assert data["1"]["new_items"] == 2
    assert data["1"]["removed_items"] == 1
    assert data["2"]["total"] == 3
    assert data["2"]["new_items"] == 0

