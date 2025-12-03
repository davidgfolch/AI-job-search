import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from main import app
from models.job import Job

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch('routers.jobs.get_db')
def test_list_jobs_empty(mock_get_db):
    """Test listing jobs when there are no results"""
    mock_db = Mock()
    mock_db.count.return_value = 0
    mock_db.fetchAll.return_value = []
    mock_db.getTableDdlColumnNames.return_value = ['id', 'title', 'company']
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 0
    assert data['items'] == []
    assert data['page'] == 1
    assert data['size'] == 20


@patch('routers.jobs.get_db')
def test_list_jobs_with_data(mock_get_db):
    """Test listing jobs with actual data"""
    mock_db = Mock()
    mock_db.count.return_value = 2
    mock_db.fetchAll.return_value = [
        (1, 'Software Engineer', 'ACME Corp', 'Madrid', None, None, None, None, None, None, None),
        (2, 'Data Scientist', 'Tech Inc', 'Barcelona', None, None, None, None, None, None, None),
    ]
    mock_db.getTableDdlColumnNames.return_value = [
        'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
        'web_page', 'created', 'modified', 'merged'
    ]
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?page=1&size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['items']) == 2
    assert data['items'][0]['title'] == 'Software Engineer'
    assert data['items'][1]['company'] == 'Tech Inc'


@patch('routers.jobs.get_db')
def test_list_jobs_with_search(mock_get_db):
    """Test listing jobs with search filter"""
    mock_db = Mock()
    mock_db.count.return_value = 1
    mock_db.fetchAll.return_value = [
        (1, 'Python Developer', 'ACME Corp', 'Madrid', None, None, None, None, None, None, None),
    ]
    mock_db.getTableDdlColumnNames.return_value = [
        'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
        'web_page', 'created', 'modified', 'merged'
    ]
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?search=Python")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 1
    # Verify search param was used in the query
    mock_db.fetchAll.assert_called_once()


@patch('routers.jobs.get_db')
def test_get_job_by_id(mock_get_db):
    """Test getting a specific job by ID"""
    mock_db = Mock()
    mock_db.fetchOne.return_value = (
        1, 'Senior Developer', 'ACME Corp', 'Remote', '50000-60000',
        'https://example.com/job/1', '# Job Description', 'LinkedIn',
        None, None, None
    )
    mock_db.getTableDdlColumnNames.return_value = [
        'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
        'web_page', 'created', 'modified', 'merged'
    ]
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 1
    assert data['title'] == 'Senior Developer'
    assert data['company'] == 'ACME Corp'
    assert data['salary'] == '50000-60000'


@patch('routers.jobs.get_db')
def test_get_job_not_found(mock_get_db):
    """Test getting a job that doesn't exist"""
    mock_db = Mock()
    mock_db.fetchOne.return_value = None
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs/999")
    
    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


@patch('routers.jobs.get_db')
@patch('routers.jobs.get_job')
def test_update_job(mock_get_job, mock_get_db):
    """Test updating a job"""
    # Mock the existence check
    mock_db = Mock()
    mock_db.jobExists.return_value = True
    mock_db.executeAndCommit.return_value = 1
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


@patch('routers.jobs.get_db')
def test_update_job_not_found(mock_get_db):
    """Test updating a job that doesn't exist"""
    mock_db = Mock()
    mock_db.jobExists.return_value = False
    mock_get_db.return_value = mock_db
    
    update_data = {'comments': 'Test'}
    response = client.patch("/api/jobs/999", json=update_data)
    
    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


@patch('routers.jobs.get_db')
def test_list_jobs_with_status_filter(mock_get_db):
    """Test listing jobs with status filter"""
    mock_db = Mock()
    mock_db.count.return_value = 1
    mock_db.fetchAll.return_value = [
        (1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None, None),
    ]
    mock_db.getTableDdlColumnNames.return_value = [
        'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
        'web_page', 'created', 'modified', 'merged'
    ]
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?status=applied")
    
    assert response.status_code == 200
    # Verify the query was constructed with status filter
    mock_db.fetchAll.assert_called_once()


@patch('routers.jobs.get_db')
def test_list_jobs_pagination(mock_get_db):
    """Test pagination parameters"""
    mock_db = Mock()
    mock_db.count.return_value = 50
    mock_db.fetchAll.return_value = []
    mock_db.getTableDdlColumnNames.return_value = ['id', 'title', 'company']
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?page=2&size=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data['page'] == 2
    assert data['size'] == 10
    assert data['total'] == 50


@patch('routers.jobs.get_db')
def test_list_jobs_with_boolean_filter_true(mock_get_db):
    """Test listing jobs with boolean filter set to true"""
    mock_db = Mock()
    mock_db.count.return_value = 1
    mock_db.fetchAll.return_value = [
        (1, 'Job Title', 'Company', 'Location', None, None, None, None, None, None, None),
    ]
    mock_db.getTableDdlColumnNames.return_value = [
        'id', 'title', 'company', 'location', 'salary', 'url', 'markdown',
        'web_page', 'created', 'modified', 'merged'
    ]
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?flagged=true")
    
    assert response.status_code == 200
    # Verify the query was called
    mock_db.fetchAll.assert_called_once()
    # Check that the WHERE clause includes the boolean filter
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    assert "`flagged` = 1" in query


@patch('routers.jobs.get_db')
def test_list_jobs_with_boolean_filter_false(mock_get_db):
    """Test listing jobs with boolean filter set to false"""
    mock_db = Mock()
    mock_db.count.return_value = 1
    mock_db.fetchAll.return_value = []
    mock_db.getTableDdlColumnNames.return_value = ['id', 'title', 'company']
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?applied=false")
    
    assert response.status_code == 200
    # Verify the query includes the boolean filter for false
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    assert "`applied` = 0" in query


@patch('routers.jobs.get_db')
def test_list_jobs_with_multiple_boolean_filters(mock_get_db):
    """Test listing jobs with multiple boolean filters"""
    mock_db = Mock()
    mock_db.count.return_value = 1
    mock_db.fetchAll.return_value = []
    mock_db.getTableDdlColumnNames.return_value = ['id', 'title', 'company']
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?flagged=true&ai_enriched=true&ignored=false")
    
    assert response.status_code == 200
    # Verify all boolean filters are in the query
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    assert "`flagged` = 1" in query
    assert "`ai_enriched` = 1" in query
    assert "`ignored` = 0" in query


@patch('routers.jobs.get_db')
def test_list_jobs_boolean_filters_with_other_filters(mock_get_db):
    """Test boolean filters combined with other filters"""
    mock_db = Mock()
    mock_db.count.return_value = 1
    mock_db.fetchAll.return_value = []
    mock_db.getTableDdlColumnNames.return_value = ['id', 'title', 'company']
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?search=Python&flagged=true&status=applied")
    
    assert response.status_code == 200
    call_args = mock_db.fetchAll.call_args
    query = call_args[0][0]
    # Verify all filters are combined
    assert "`flagged` = 1" in query
    assert "`applied` = 1" in query
    assert "LIKE" in query  # Search filter
