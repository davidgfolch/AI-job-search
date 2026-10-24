from unittest.mock import patch


def test_jobs_history_route_exists():
    from api.jobs_history import router
    assert router is not None

def test_get_service_returns_service():
    from api.jobs_history import get_service
    from services.salary_history_service import SalaryHistoryService
    assert isinstance(get_service(), SalaryHistoryService)


@patch('services.salary_history_service.SalaryHistoryService.delete_record', return_value=True)
def test_delete_history_record(mock_delete, client):
    response = client.delete("/api/jobs/history/abc123")
    assert response.status_code == 200
    assert response.json() == {"deleted": 1}
    mock_delete.assert_called_once_with("abc123")


@patch('services.salary_history_service.SalaryHistoryService.delete_record', return_value=False)
def test_delete_history_record_not_found(mock_delete, client):
    response = client.delete("/api/jobs/history/abc123")
    assert response.status_code == 404
    assert response.json()["detail"] == "Salary history record not found"
