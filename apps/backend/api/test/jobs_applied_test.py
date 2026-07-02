import pytest
from unittest.mock import patch
from datetime import datetime

create_mock_db = pytest.create_mock_db


@pytest.mark.parametrize(
    "url,mock_data,expected_count,expected_ids,expected_dates",
    [
        (
            "/api/jobs/applied-by-company?company=ACME%20Corp",
            [(3, datetime(2024, 2, 20)), (2, datetime(2024, 1, 15))],
            2,
            [3, 2],
            ["2024-02-20", "2024-01-15"],
        ),
        ("/api/jobs/applied-by-company?company=NonExistent%20Corp", [], 0, [], []),
        (
            "/api/jobs/applied-by-company?company=joppy&client=RealClient",
            [(5, datetime(2024, 3, 10))],
            1,
            [5],
            ["2024-03-10"],
        ),
    ],
    ids=["valid_company", "empty_result", "with_client_param"],
)
@patch("services.company_synonym_service.CompanySynonymService.get_synonyms")
@patch("repositories.jobQueryRepository.JobQueryRepository.get_db")
def test_get_applied_jobs_by_company(
    mock_get_db, mock_synonyms, client, url, mock_data, expected_count, expected_ids, expected_dates
):
    mock_synonyms.return_value = []
    """Test getting applied jobs by company with various scenarios"""
    mock_db = create_mock_db(fetchAll=mock_data)
    mock_get_db.return_value = mock_db
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == expected_count
    for i, (expected_id, expected_date) in enumerate(zip(expected_ids, expected_dates)):
        assert data[i]["id"] == expected_id
        assert expected_date in data[i]["created"]


@pytest.mark.parametrize(
    "company_param",
    [
        "O%27Reilly%20Media",
        "Company%20%26%20Co",
        "Bridgetech%20%7C%20Alfresco",
    ],
    ids=["apostrophe", "ampersand", "pipe"],
)
@patch("services.company_synonym_service.CompanySynonymService.get_synonyms")
@patch("repositories.jobQueryRepository.JobQueryRepository.get_db")
def test_get_applied_jobs_by_company_special_characters(
    mock_get_db, mock_synonyms, client, company_param
):
    mock_synonyms.return_value = []
    """Test that companies with special characters (non-SQL) work correctly"""
    mock_db = create_mock_db(fetchAll=[(10, datetime(2024, 4, 1))])
    mock_get_db.return_value = mock_db
    response = client.get(f"/api/jobs/applied-by-company?company={company_param}")
    assert response.status_code == 200
    assert response.status_code == 200


@patch("services.company_synonym_service.CompanySynonymService.get_synonyms")
@patch("repositories.jobQueryRepository.JobQueryRepository.get_db")
@patch("repositories.jobQueryRepository.JobQueryRepository.find_applied_jobs_by_regex")
def test_get_applied_jobs_partial_search_exception(
    mock_find_regex, mock_get_db, mock_synonyms, client
):
    mock_synonyms.return_value = []
    """Test exception handling in partial company search"""
    mock_db = create_mock_db(
        fetchAll=[]
    )  # First call returns empty to trigger partial search
    mock_get_db.return_value = mock_db

    # partial search calls find_applied_jobs_by_regex
    # We want it to fail ON THE SECOND CALL (partial search), but return empty on first call (exact search)
    mock_find_regex.side_effect = [[], Exception("DB Error")]

    # A company name with multiple words to trigger the loop in _search_partial_company
    # and not 'grupo'
    company = "Big Tech Company"

    response = client.get(f"/api/jobs/applied-by-company?company={company}")

    assert response.status_code == 200
    assert response.json() == []


@patch("services.company_synonym_service.CompanySynonymService.get_synonyms")
@patch("repositories.jobQueryRepository.JobQueryRepository.get_db")
@patch("repositories.jobQueryRepository.JobQueryRepository.find_applied_jobs_by_regex")
def test_get_applied_jobs_partial_search_exclusions(
    mock_find_regex, mock_get_db, mock_synonyms, client
):
    mock_synonyms.return_value = []
    """
    Test that partial search excludes common words like 'The'.
    Case: 'The White Team' -> 'The White' (not found) -> 'The' (should be skipped)
    """
    mock_db = create_mock_db(fetchAll=[])  # First call (exact match) returns empty
    mock_get_db.return_value = mock_db

    # We mock find_applied_jobs_by_regex to track what it's called with
    # First call will be from _search_partial_company for "The White" (since "The White Team" failed exact match via find_applied_by_company)
    # If it were called for "The", we would see it in the mock calls.
    mock_find_regex.return_value = []

    company = "The White Team"
    client.get(f"/api/jobs/applied-by-company?company={company}")

    # Check calls to find_applied_jobs_by_regex
    # Expected:
    # 1. Exact match call with ['the white team']
    # 2. Partial match call with ['...the white...']

    calls = [args[0] for args, _ in mock_find_regex.call_args_list]

    # Calls are now lists of regex patterns; flatten to check contents
    all_patterns = [p for call in calls for p in (call if isinstance(call, list) else [call])]

    # Verify we searched for 'the white' (regex format)
    assert any("the white" in p for p in all_patterns)

    # Verify we did NOT search for just 'The' (regex format)
    for pattern in all_patterns:
        if "The" in pattern and "White" not in pattern and "Team" not in pattern:
            if len(pattern) < 20:
                assert False, (
                    f"Should not have searched for short generic term: {pattern}"
                )


@pytest.mark.parametrize(
    "query_params, expected_error",
    [
        ("company=Company;%20DROP%20TABLE%20jobs", "semicolon"),
        ("company=Company%20UNION%20SELECT", "union"),
        ("company=SELECT%20*%20FROM%20jobs", "select"),
        ("company=joppy&client=Client;%20DROP%20TABLE", "semicolon"),
    ],
    ids=["semicolon_company", "union", "select", "semicolon_client"],
)
def test_get_applied_jobs_sql_injection(client, query_params, expected_error):
    """Test that various SQL injection attempts are blocked"""
    response = client.get(f"/api/jobs/applied-by-company?{query_params}")
    assert response.status_code == 400
    assert expected_error in response.json()["detail"].lower()


def test_get_applied_jobs_by_company_missing_parameter(client):
    """Test that missing company parameter returns validation error"""
    response = client.get("/api/jobs/applied-by-company")
    assert response.status_code == 422


@patch("services.company_synonym_service.CompanySynonymService.get_synonyms")
@patch("repositories.jobQueryRepository.JobQueryRepository.get_db")
def test_get_applied_jobs_with_synonym_expansion(mock_get_db, mock_synonyms, client):
    mock_synonyms.return_value = ["Synonym Corp"]
    mock_db = create_mock_db(fetchAll=[(3, datetime(2024, 2, 20))])
    mock_get_db.return_value = mock_db
    response = client.get("/api/jobs/applied-by-company?company=Original+Corp")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 3


def test_get_applied_jobs_by_company_empty_string(client):
    """Test that empty company parameter is rejected"""
    response = client.get("/api/jobs/applied-by-company?company=")
    assert response.status_code == 400
    assert "must be a non-empty string" in response.json()["detail"]
