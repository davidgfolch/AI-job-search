from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_calculate_salary_api():
    response = client.post(
        "/api/salary/calculate",
        json={
            "rate": 40,
            "rate_type": "Hourly",
            "hours_x_day": 8,
            "freelance_rate": 80
        }
    )
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "gross_year" in data
    assert "net_year" in data
    assert data["parsed_equation"] == "40.0 * 8.0 * 23.3 * 11"

def test_calculate_salary_api_daily():
    response = client.post(
        "/api/salary/calculate",
        json={
            "rate": 300,
            "rate_type": "Daily",
            "hours_x_day": 8,
            "freelance_rate": 80
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "gross_year" in data
