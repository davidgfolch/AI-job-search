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
