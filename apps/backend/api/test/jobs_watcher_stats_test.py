import pytest
from unittest.mock import MagicMock
from main import app
from api.jobs import get_service


def test_get_watcher_stats(client):
    """Test get_watcher_stats endpoint returns total and new_items counts"""
    mock_service = MagicMock()
    mock_service.get_watcher_stats.return_value = {"total": 100, "new_items": 5}
    
    app.dependency_overrides[get_service] = lambda: mock_service
    
    try:
        response = client.get("/api/jobs/watcher-stats?search=developer&watcher_cutoff=2023-01-01")
        
        assert response.status_code == 200
        assert response.json() == {"total": 100, "new_items": 5}
        mock_service.get_watcher_stats.assert_called_once()
        call_args = mock_service.get_watcher_stats.call_args[1]
        assert call_args['search'] == 'developer'
        assert call_args['watcher_cutoff'] == '2023-01-01'
    finally:
        app.dependency_overrides = {}
