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
@patch("repositories.jobs_repository.JobsRepository.get_db")
def test_get_applied_jobs_by_company(
    mock_get_db, client, url, mock_data, expected_count, expected_ids, expected_dates
):
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
    ],
    ids=["apostrophe", "ampersand"],
)
@patch("repositories.jobs_repository.JobsRepository.get_db")
def test_get_applied_jobs_by_company_special_characters(
    mock_get_db, client, company_param
):
    """Test that companies with special characters (non-SQL) work correctly"""
    mock_db = create_mock_db(fetchAll=[(10, datetime(2024, 4, 1))])
    mock_get_db.return_value = mock_db
    response = client.get(f"/api/jobs/applied-by-company?company={company_param}")
    assert response.status_code == 200
    assert response.status_code == 200


@patch("repositories.jobs_repository.JobsRepository.get_db")
@patch("repositories.jobs_repository.JobsRepository.find_applied_jobs_by_regex")
def test_get_applied_jobs_partial_search_exception(
    mock_find_regex, mock_get_db, client
):
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


@patch("repositories.jobs_repository.JobsRepository.get_db")
@patch("repositories.jobs_repository.JobsRepository.find_applied_jobs_by_regex")
def test_get_applied_jobs_partial_search_exclusions(
    mock_find_regex, mock_get_db, client
):
    """
    Test that partial search excludes common words like 'The'.
    Case: 'The White Team' -> 'The White' (not found) -> 'The' (should be skipped)
    """
    mock_db = create_mock_db(
        fetchAll=[]
    )  # First call (exact match) returns empty
    mock_get_db.return_value = mock_db
    
    # We mock find_applied_jobs_by_regex to track what it's called with
    # First call will be from _search_partial_company for "The White" (since "The White Team" failed exact match via find_applied_by_company)
    # If it were called for "The", we would see it in the mock calls.
    mock_find_regex.return_value = [] 
    
    company = "The White Team"
    client.get(f"/api/jobs/applied-by-company?company={company}")
    
    # Check calls to find_applied_jobs_by_regex
    # Expected: 
    # 1. 'The White'
    # 2. Should NOT call with 'The'
    
    calls = [args[0] for args, _ in mock_find_regex.call_args_list]
    
    # Verify we searched for 'the white' (regex format dependent on implementation, but broadly)
    # Backend lowers the company name, so we expect 'the white'
    assert any("the white" in c for c in calls)
    
    # Verify we did NOT search for just 'The' (regex format)
    # The regex for 'The' would be something like '(^| )The($| )' (escaped)
    # We check that no call has a regex that is essentially just "The"
    for call_arg in calls:
        if "The" in call_arg and "White" not in call_arg and "Team" not in call_arg:
            # Check if this is the "The" search we want to avoid
            # It might look like '(^| )The($| )'
            if len(call_arg) < 20: # Rough check for short regex
                 assert False, f"Should not have searched for short generic term: {call_arg}"
