from unittest.mock import patch

SERVICE = "api.dashboard.service"

DASHBOARD_DATA = {
    "services": [{"name": "aienrich", "displayName": "AI Enrich", "status": "running", "metrics": {}}],
    "ollama": {"reachable": True, "recentErrors": []},
    "timestamp": "2026-09-03T10:00:00",
}


def test_get_services_status(client):
    with patch(f"{SERVICE}.get_services_status", return_value=DASHBOARD_DATA):
        response = client.get("/api/dashboard/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert data["services"][0]["status"] == "running"
    assert data["ollama"]["reachable"] is True
