from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_timezone():
    response = client.get("/api/system/timezone")
    assert response.status_code == 200
    data = response.json()
    assert "offset_minutes" in data
    assert isinstance(data["offset_minutes"], int)
