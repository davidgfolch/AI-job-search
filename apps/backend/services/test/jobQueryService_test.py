import pytest
from unittest.mock import MagicMock
from services.jobQueryService import JobQueryService
from repositories.jobQueryRepository import JobQueryRepository
from services.company_synonym_service import CompanySynonymService


@pytest.fixture
def mock_repo():
    return MagicMock(spec=JobQueryRepository)


@pytest.fixture
def mock_synonym_service():
    svc = MagicMock(spec=CompanySynonymService)
    svc.get_synonyms.return_value = []
    return svc


@pytest.fixture
def service(mock_repo, mock_synonym_service):
    svc = JobQueryService(synonym_service=mock_synonym_service)
    svc.query_repo = mock_repo
    return svc


def test_get_applied_jobs_by_company_name(service, mock_repo):
    mock_repo.find_applied_by_companies.return_value = [(1, None), (2, None)]

    result = service.get_applied_jobs_by_company_name("test")

    assert len(result) == 2
    mock_repo.find_applied_by_companies.assert_called_once()


def test_get_applied_jobs_by_company_name_empty_company(service):
    with pytest.raises(ValueError):
        service.get_applied_jobs_by_company_name("")


def test_get_applied_jobs_by_company_name_none_repo_result(service, mock_repo):
    mock_repo.find_applied_by_companies.return_value = None
    mock_repo.find_applied_jobs_by_regex.return_value = None

    result = service.get_applied_jobs_by_company_name("unknown-company")

    assert result == []


def test_get_applied_jobs_with_synonyms(service, mock_repo, mock_synonym_service):
    mock_synonym_service.get_synonyms.return_value = ["Synonym Corp"]
    mock_repo.find_applied_by_companies.return_value = [(1, None)]

    result = service.get_applied_jobs_by_company_name("Original Corp")

    assert len(result) == 1
    mock_repo.find_applied_by_companies.assert_called_once_with(
        ["original corp", "Synonym Corp"]
    )


def test_get_applied_jobs_with_synonyms_partial_fallback(service, mock_repo, mock_synonym_service):
    mock_synonym_service.get_synonyms.return_value = ["Synonym Corp"]
    mock_repo.find_applied_by_companies.return_value = None
    mock_repo.find_applied_jobs_by_regex.return_value = [(2, None)]

    result = service.get_applied_jobs_by_company_name("Original Corp")

    assert len(result) == 1
    mock_repo.find_applied_by_companies.assert_called_once()
    assert mock_repo.find_applied_jobs_by_regex.called


def test_joppy_special_case_ignores_synonyms(service, mock_repo, mock_synonym_service):
    mock_repo.find_applied_by_company.return_value = [(1, None)]

    result = service.get_applied_jobs_by_company_name("joppy", client="RealClient")

    assert len(result) == 1
    mock_repo.find_applied_by_company.assert_called_once_with("RealClient", "RealClient")
    mock_synonym_service.get_synonyms.assert_not_called()
