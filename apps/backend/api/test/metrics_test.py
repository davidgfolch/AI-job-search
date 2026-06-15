from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_enrichment_metrics_no_data():
    response = client.get("/api/enrichment/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "no_data"
    assert "message" in data
