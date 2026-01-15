import pytest
from unittest.mock import patch, MagicMock
from services.jobs_service import JobsService
from api.jobs import BulkJobUpdate, JobUpdate

@patch('services.jobs_service.JobsRepository')
def test_bulk_update_jobs_by_ids(mock_repo_cls):
    """Test bulk update by IDs"""
    mock_repo = mock_repo_cls.return_value
    service = JobsService(repo=mock_repo)
    
    update_data = {'ignored': True}
    ids = [1, 2, 3]
    
    # Mock return
    mock_repo.update_jobs_by_ids.return_value = 3
    
    count = service.bulk_update_jobs(
        update_data=update_data,
        ids=ids,
        select_all=False
    )
    
    assert count == 3
    mock_repo.update_jobs_by_ids.assert_called_once_with(ids, update_data)
    mock_repo.build_where.assert_not_called()
    mock_repo.update_jobs_by_filter.assert_not_called()

@patch('services.jobs_service.JobsRepository')
def test_bulk_update_jobs_select_all(mock_repo_cls):
    """Test bulk update with select_all=True"""
    mock_repo = mock_repo_cls.return_value
    service = JobsService(repo=mock_repo)
    
    update_data = {'ignored': True}
    filters = {'search': 'python', 'ignored': False}
    
    # Mock build_where return
    mock_repo.build_where.return_value = (["search LIKE %s", "ignored = 0"], ["%python%"])
    # Mock update return
    mock_repo.update_jobs_by_filter.return_value = 10
    
    count = service.bulk_update_jobs(
        update_data=update_data,
        filters=filters,
        select_all=True
    )
    
    assert count == 10
    mock_repo.build_where.assert_called_once()
    mock_repo.update_jobs_by_filter.assert_called_once()
    args, _ = mock_repo.update_jobs_by_filter.call_args
    assert args[0] == ["search LIKE %s", "ignored = 0"] # where clauses
    assert args[1] == ["%python%"] # params
    assert args[2] == update_data

def test_bulk_update_api(client):
    """Test bulk update API endpoint"""
    with patch('services.jobs_service.JobsService.bulk_update_jobs') as mock_bulk_update:
        mock_bulk_update.return_value = 5
        
        payload = {
            "ids": [1, 2],
            "update": {"ignored": True},
            "select_all": False
        }
        
        response = client.post("/api/jobs/bulk", json=payload)
        
        assert response.status_code == 200
        assert response.json() == {"updated": 5}
        mock_bulk_update.assert_called_once()
