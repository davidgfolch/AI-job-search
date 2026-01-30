import pytest
from unittest.mock import patch, MagicMock

create_mock_db = pytest.create_mock_db
JOB_COLUMNS = pytest.JOB_COLUMNS

@patch('repositories.jobs_repository.JobsRepository.get_db')
def test_list_jobs_by_ids(mock_get_db, client):
    """Test listing jobs filtered by specific IDs"""
    # Create mock DB that checks the query contains "id IN"
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    mock_db.__exit__.return_value = None
    
    # Mock count return
    mock_db.count.return_value = 2
    
    # Mock fetchAll return (jobs) and columns
    mock_db.fetchAll.side_effect = [
        # First call for fetch_jobs
        [
            (1, 'Target Job 1', 'Company A', 'Remote', None, None, None, None, None, None, None),
            (3, 'Target Job 3', 'Company B', 'Remote', None, None, None, None, None, None, None),
        ],
        # Second call for columns
        [(col,) for col in JOB_COLUMNS]
    ]
    
    mock_get_db.return_value = mock_db
    
    # Request with ids param (FastAPI Query param for list usually looks like ?ids=1&ids=3)
    response = client.get("/api/jobs?ids=1&ids=3")
    
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['items']) == 2
    assert data['items'][0]['id'] == 1
    assert data['items'][1]['id'] == 3
    
    # Verify the SQL query generated contained the ID filter
    call_args = mock_db.fetchAll.call_args_list[0]
    query = call_args[0][0]
    params = call_args[0][1]
    
    assert "id IN (%s, %s)" in query
    assert 1 in params
    assert 3 in params
