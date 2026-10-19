from unittest.mock import patch

SERVICE = "api.dashboard.service"

DASHBOARD_DATA = {
    "services": [{
        "name": "aienrich",
        "displayName": "AI Enrich",
        "status": "running",
        "usesOllama": True,
        "deployment": "docker",
        "lastActivity": None,
        "metrics": {},
        "recentErrors": [],
    }],
    "ollama": {
        "reachable": True,
        "serverUrl": "http://192.168.1.45:11434",
        "serverIp": "192.168.1.45",
        "isLan": True,
        "recentErrors": [],
    },
    "prometheus": {"reachable": True, "url": "http://localhost:9090"},
    "grafana": {"reachable": True, "url": "http://localhost:3000"},
    "timestamp": "2026-09-03T10:00:00",
    "deployment": "docker",
}


def test_get_services_status(client):
    with patch(f"{SERVICE}.get_services_status", return_value=DASHBOARD_DATA):
        response = client.get("/api/dashboard/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert data["services"][0]["status"] == "running"
    assert data["services"][0]["deployment"] == "docker"
    assert data["ollama"]["reachable"] is True
    assert data["ollama"]["serverIp"] == "192.168.1.45"
    assert data["ollama"]["isLan"] is True
    assert data["prometheus"]["reachable"] is True
    assert data["prometheus"]["url"] == "http://localhost:9090"
    assert data["grafana"]["reachable"] is True
    assert data["grafana"]["url"] == "http://localhost:3000"
    assert data["deployment"] == "docker"
