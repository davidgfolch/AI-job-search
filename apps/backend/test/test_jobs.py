import pytest
from unittest.mock import patch

from unittest.mock import patch, MagicMock
from repositories.jobs_repository import JobsRepository

create_mock_db = pytest.create_mock_db
JOB_COLUMNS = pytest.JOB_COLUMNS


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch('repositories.jobs_repository.MysqlUtil')
@patch('repositories.jobs_repository.getConnection')
def test_get_db(mock_get_connection, mock_mysql_util):
    """Test the get_db method"""
    repo = JobsRepository()
    mock_conn = MagicMock()
    mock_get_connection.return_value = mock_conn
    
    repo.get_db()
    
    mock_get_connection.assert_called_once()
    mock_mysql_util.assert_called_once_with(mock_conn)


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_empty(mock_get_db, client):
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


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_with_data(mock_get_db, client):
    """Test listing jobs with actual data"""
    mock_db = create_mock_db(
        count=2,
        fetchAll=[
            (1, 'Software Engineer', 'ACME Corp', 'Madrid', None, None, None, None, None, None, None),
            (2, 'Data Scientist', 'Tech Inc', 'Barcelona', None, None, None, None, None, None, None),
        ],
        columns=JOB_COLUMNS
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs?page=1&size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['items']) == 2
    assert data['items'][0]['title'] == 'Software Engineer'
    assert data['items'][1]['company'] == 'Tech Inc'


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_get_job_by_id(mock_get_db, client):
    """Test getting a specific job by ID"""
    mock_db = create_mock_db(
        fetchOne=(
            1, 'Senior Developer', 'ACME Corp', 'Remote', '50000-60000',
            'https://example.com/job/1', '# Job Description', 'LinkedIn',
            None, None, None
        ),
        columns=JOB_COLUMNS
    )
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 1
    assert data['title'] == 'Senior Developer'
    assert data['company'] == 'ACME Corp'
    assert data['salary'] == '50000-60000'


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_get_job_not_found(mock_get_db, client):
    """Test getting a job that doesn't exist"""
    mock_db = create_mock_db(fetchOne=None)
    mock_get_db.return_value = mock_db
    
    response = client.get("/api/jobs/999")
    
    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'


@patch('repositories.jobs_repository.JobsRepository.get_db')
@patch('services.jobs_service.JobsService.get_job')
def test_update_job(mock_get_job, mock_get_db, client):
    """Test updating a job"""
    mock_db = create_mock_db(fetchOne=(1,))
    mock_get_db.return_value = mock_db
    
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
    mock_db.executeAndCommit.assert_called_once()


@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_update_job_not_found(mock_get_db, client):
    """Test updating a job that doesn't exist"""
    mock_db = create_mock_db(fetchOne=None)
    mock_get_db.return_value = mock_db
    
    update_data = {'comments': 'Test'}
    response = client.patch("/api/jobs/999", json=update_data)
    
    assert response.status_code == 404
    assert response.json()['detail'] == 'Job not found'
    assert response.json()['detail'] == 'Job not found'


@patch('repositories.jobs_repository.JobsRepository.get_db')
@patch('services.jobs_service.JobsService.get_job')
def test_update_job_empty_data(mock_get_job, mock_get_db, client):
    """Test updating a job with no data"""
    mock_db = create_mock_db(fetchOne=(1,))
    mock_get_db.return_value = mock_db
    mock_get_job.return_value = {'id': 1} # Mock return of get_job

    response = client.patch("/api/jobs/1", json={})
    
    assert response.status_code == 200
    # Should not call executeAndCommit
    mock_db.executeAndCommit.assert_not_called()


@patch('repositories.jobs_repository.JobsRepository.get_db')
@patch('services.jobs_service.JobsService.delete_jobs')
def test_bulk_delete_jobs(mock_delete_jobs, mock_get_db, client):
    """Test bulk deleting jobs"""
    mock_db = create_mock_db(fetchOne=(1,))
    mock_get_db.return_value = mock_db
    mock_delete_jobs.return_value = 5

    payload = {
        'ids': [1, 2, 3],
        'select_all': False
    }
    
    response = client.post("/api/jobs/bulk/delete", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"deleted": 5}
    mock_delete_jobs.assert_called_once()

