import pytest
from unittest.mock import MagicMock
from services.jobQueryService import JobQueryService
from repositories.jobQueryRepository import JobQueryRepository


@pytest.fixture
def mock_repo():
    return MagicMock(spec=JobQueryRepository)


@pytest.fixture
def service(mock_repo):
    service = JobQueryService()
    service.query_repo = mock_repo
    return service


def test_get_applied_jobs_by_company_name(service, mock_repo):
    mock_repo.find_applied_by_company.return_value = [(1, None), (2, None)]

    result = service.get_applied_jobs_by_company_name("test")

    assert len(result) == 2
    mock_repo.find_applied_by_company.assert_called_once()


def test_get_applied_jobs_by_company_name_empty_company(service):
    with pytest.raises(ValueError):
        service.get_applied_jobs_by_company_name("")
