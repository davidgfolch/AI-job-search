import pytest
from unittest.mock import patch

create_mock_db = pytest.create_mock_db


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_search(mock_get_db, client):
    """Test listing jobs with search filter"""
    mock_db = create_mock_db(
        count=1,
        fetchAll=[
            (1, 'Python Developer', 'ACME Corp', 'Madrid', None, None, None, None, None, None, None),
        ],
        columns=[
            'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
            'web_page', 'created', 'modified', 'merged'
        ]
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?search=Python")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 1
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    assert "LIKE" in matched_query


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_status_filter(mock_get_db, client):
    """Test listing jobs with status filter"""
    mock_db = create_mock_db(
        count=1,
        fetchAll=[
            (1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None, None),
        ],
        columns=[
            'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
            'web_page', 'created', 'modified', 'merged'
        ]
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?status=applied")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any("`applied` = 1" in q for q in queries)


@patch('services.jobs_service.JobsService.get_db')
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


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_boolean_filter_true(mock_get_db, client):
    """Test listing jobs with boolean filter set to true"""
    mock_db = create_mock_db(
        count=1,
        fetchAll=[
            (1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None, None),
        ],
        columns=[
            'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
            'web_page', 'created', 'modified', 'merged'
        ]
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?flagged=true")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any("`flagged` = 1" in q for q in queries)


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_boolean_filter_false(mock_get_db, client):
    """Test listing jobs with boolean filter set to false"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?applied=false")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any("`applied` = 0" in q for q in queries)


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_multiple_boolean_filters(mock_get_db, client):
    """Test listing jobs with multiple boolean filters"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?flagged=true&ai_enriched=true&ignored=false")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    assert "`flagged` = 1" in matched_query
    assert "`ai_enriched` = 1" in matched_query
    assert "`ignored` = 0" in matched_query


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_boolean_filters_with_other_filters(mock_get_db, client):
    """Test boolean filters combined with other filters"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?search=Python&flagged=true&status=applied")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    assert "`flagged` = 1" in matched_query
    assert "`applied` = 1" in matched_query
    assert "LIKE" in matched_query
