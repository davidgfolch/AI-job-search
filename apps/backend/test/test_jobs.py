import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app
from models.job import Job

client = TestClient(app)

def create_mock_db(**kwargs):
    """Helper to create a mock database that supports context manager"""
    mock_db = Mock()
    columns = kwargs.get('columns', ['id', 'title', 'company'])
    data_rows = kwargs.get('fetchAll', [])
    
    def fetch_all_side_effect(query, params=None):
        if "SHOW COLUMNS" in str(query).upper():
            return [(c,) for c in columns]
        return data_rows

    mock_db.count.return_value = kwargs.get('count', 0)
    mock_db.fetchAll.side_effect = fetch_all_side_effect
    mock_db.fetchOne.return_value = kwargs.get('fetchOne', None)
    mock_db.getTableDdlColumnNames.return_value = columns
    mock_db.executeAndCommit.return_value = kwargs.get('executeAndCommit', 1)
    # Support context manager
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=False)
    return mock_db


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_empty(mock_get_db):
    """Test listing jobs when there are no results"""
    mock_db = create_mock_db(count=0, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 0
    assert data['items'] == []
    assert data['page'] == 1
    assert data['size'] == 20


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_data(mock_get_db):
    """Test listing jobs with actual data"""
    mock_db = create_mock_db(
        count=2,
        fetchAll=[
            (1, 'Software Engineer', 'ACME Corp', 'Madrid', None, None, None, None, None, None, None),
            (2, 'Data Scientist', 'Tech Inc', 'Barcelona', None, None, None, None, None, None, None),
        ],
        columns=[
            'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
            'web_page', 'created', 'modified', 'merged'
        ]
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?page=1&size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['items']) == 2
    assert data['items'][0]['title'] == 'Software Engineer'
    assert data['items'][1]['company'] == 'Tech Inc'


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_search(mock_get_db):
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
    # Verify search param was used in the query
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    assert "LIKE" in matched_query


@patch('services.jobs_service.JobsService.get_db')
def test_get_job_by_id(mock_get_db):
    """Test getting a specific job by ID"""
    mock_db = create_mock_db(
        fetchOne=(
            1, 'Senior Developer', 'ACME Corp', 'Remote', '50000-60000',
            'https://example.com/job/1', '# Job Description', 'LinkedIn',
            None, None, None
        ),
        columns=[
            'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
            'web_page', 'created', 'modified', 'merged'
        ]
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 1
    assert data['title'] == 'Senior Developer'
    assert data['company'] == 'ACME Corp'
    assert data['salary'] == '50000-60000'


@patch('services.jobs_service.JobsService.get_db')
def test_get_job_not_found(mock_get_db):
    """Test getting a job that doesn't exist"""
    mock_db = create_mock_db(fetchOne=None)
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs/999")
    
    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


@patch('services.jobs_service.JobsService.get_db')
@patch('services.jobs_service.JobsService.get_job')
def test_update_job(mock_get_job, mock_get_db):
    """Test updating a job"""
    # Mock the existence check
    mock_db = create_mock_db(fetchOne=(1,))
    mock_get_db.return_value = mock_db
    
    # Mock the get_job function that's called after update
    updated_job_data = {
        'id': 1,
        'title': 'Senior Developer',
        'company': 'ACME Corp',
        'comments': 'Updated comment',
        'applied': True
    }
    mock_get_job.return_value = updated_job_data
    
    update_data = {
        'comments': 'Updated comment',
        'applied': True
    }
    
    response = client.patch("/api/jobs/1", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data['comments'] == 'Updated comment'
    assert data['applied'] == True
    
    # Verify executeAndCommit was called
    mock_db.executeAndCommit.assert_called_once()


@patch('services.jobs_service.JobsService.get_db')
def test_update_job_not_found(mock_get_db):
    """Test updating a job that doesn't exist"""
    mock_db = create_mock_db(fetchOne=None)
    mock_get_db.return_value = mock_db
    
    update_data = {'comments': 'Test'}
    response = client.patch("/api/jobs/999", json=update_data)
    
    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_status_filter(mock_get_db):
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
    # Verify the query was constructed with status filter
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any("`applied` = 1" in q for q in queries)


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_pagination(mock_get_db):
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
def test_list_jobs_with_boolean_filter_true(mock_get_db):
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
    # Verify the query was called
    # Check that ANY of the queries includes the boolean filter
    # The first call might be for columns or count
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any("`flagged` = 1" in q for q in queries)

@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_boolean_filter_false(mock_get_db):
    """Test listing jobs with boolean filter set to false"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?applied=false")
    
    assert response.status_code == 200
    # Verify the query includes the boolean filter for false
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    assert any("`applied` = 0" in q for q in queries)


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_with_multiple_boolean_filters(mock_get_db):
    """Test listing jobs with multiple boolean filters"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?flagged=true&ai_enriched=true&ignored=false")
    
    assert response.status_code == 200
    # Verify all boolean filters are in the query
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    assert "`flagged` = 1" in matched_query
    assert "`ai_enriched` = 1" in matched_query
    assert "`ignored` = 0" in matched_query


@patch('services.jobs_service.JobsService.get_db')
def test_list_jobs_boolean_filters_with_other_filters(mock_get_db):
    """Test boolean filters combined with other filters"""
    mock_db = create_mock_db(count=1, fetchAll=[], columns=['id', 'title', 'company'])
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?search=Python&flagged=true&status=applied")
    
    assert response.status_code == 200
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    matched_query = next((q for q in queries if "SELECT" in q and "FROM" in q), "")
    # Verify all filters are combined
    assert "`flagged` = 1" in matched_query
    assert "`applied` = 1" in matched_query
    assert "LIKE" in matched_query  # Search filter
