import pytest
from unittest.mock import patch

create_mock_db = pytest.create_mock_db


@patch('repositories.jobs_repository.JobsRepository.get_db')
@pytest.mark.parametrize("query_param, expected_query_part", [
    ("search=Python", "LIKE"),
    ("status=applied", "`applied` = 1"),
    ("not_status=applied", "`applied` = 0"),
    ("sql_filter=salary > 1000", "(salary > 1000)"),
], ids=["search", "status", "not_status", "sql_filter"])
def test_list_jobs_with_single_filters(mock_get_db, client, query_param, expected_query_part):
    """Test listing jobs with various single filters"""
    mock_db = create_mock_db(
        count=1,
        fetchAll=[(1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None, None)],
        columns=['id', 'title', 'company', 'location', 'salary', 'url', 'markdown', 'web_page', 'created', 'modified', 'merged']
    )
    mock_get_db.return_value = mock_db
    
    response = client.get(f"/api/jobs?{query_param}")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    # Check if any query contains the expected part
    matched = any(expected_query_part in q for q in queries)
    assert matched, f"Expected '{expected_query_part}' in queries: {queries}"


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_pagination(mock_get_db, client):
    """Test pagination parameters"""
    mock_db = create_mock_db(
        count=50,
        fetchAll=[],
        columns=['id', 'title', 'company']
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?page=2&size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 2
    assert data['size'] == 10
    assert data['total'] == 50


@patch('repositories.jobs_repository.JobsRepository.get_db')
@pytest.mark.parametrize("query_params, expected_conditions", [
    ("flagged=true", ["`flagged` = 1"]),
    ("applied=false", ["`applied` = 0"]),
    ("flagged=true&ai_enriched=true&ignored=false", ["`flagged` = 1", "`ai_enriched` = 1", "`ignored` = 0"]),
    ("search=Python&flagged=true&status=applied", ["LIKE", "`flagged` = 1", "`applied` = 1"]),
], ids=["bool_true", "bool_false", "multiple_bool", "mixed_filters"])
def test_list_jobs_with_combined_filters(mock_get_db, client, query_params, expected_conditions):
    """Test listing jobs with boolean and combined filters"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get(f"/api/jobs?{query_params}")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    
    for condition in expected_conditions:
        assert condition in matched_query

