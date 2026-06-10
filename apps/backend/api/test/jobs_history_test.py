def test_jobs_history_route_exists():
    from api.jobs_history import router
    assert router is not None

def test_get_service_returns_service():
    from api.jobs_history import get_service
    from services.salary_history_service import SalaryHistoryService
    assert isinstance(get_service(), SalaryHistoryService)
