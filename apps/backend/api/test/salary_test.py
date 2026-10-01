from unittest.mock import patch

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


def test_calculate_salary_failure_is_logged(log_records):
    with patch("services.salary_service.SalaryService.calculate_salary", side_effect=ValueError("bad rate")):
        response = client.post(
            "/api/salary/calculate",
            json={"rate": 0, "rate_type": "Hourly", "hours_x_day": 8, "freelance_rate": 80}
        )
    assert response.status_code == 500
    records = log_records(event="salary.calculation_failed")
    assert len(records) == 1
    assert records[0]["level"] == "error"
    assert records[0]["error"] == "bad rate"
    assert records[0]["rate_type"] == "Hourly"
    assert "ValueError" in records[0]["exception"]
