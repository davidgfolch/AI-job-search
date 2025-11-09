import pytest
from unittest.mock import Mock
from commonlib.services.job_service import JobService
from commonlib.repository.job_repository import Job, JobRepository

class TestJobService:
    def test_get_job_by_id_valid(self):
        mock_repo = Mock(spec=JobRepository)
        mock_job = Job(id=1, title="Test Job")
        mock_repo.find_by_id.return_value = mock_job
        
        service = JobService(mock_repo)
        result = service.get_job_by_id(1)
        
        assert result == mock_job
        mock_repo.find_by_id.assert_called_once_with(1)
    
    def test_get_job_by_id_invalid(self):
        mock_repo = Mock(spec=JobRepository)
        service = JobService(mock_repo)
        
        with pytest.raises(ValueError, match="Job ID must be positive"):
            service.get_job_by_id(-1)
    
    def test_search_jobs(self):
        mock_repo = Mock(spec=JobRepository)
        mock_jobs = [Job(id=1, title="Job 1"), Job(id=2, title="Job 2")]
        mock_repo.find_all.return_value = mock_jobs
        
        service = JobService(mock_repo)
        filters = {"company": "Test Corp"}
        result = service.search_jobs(filters)
        
        assert result == mock_jobs
        mock_repo.find_all.assert_called_once_with(filters)
    
    def test_delete_job_success(self):
        mock_repo = Mock(spec=JobRepository)
        mock_job = Job(id=1, title="Test Job")
        mock_repo.find_by_id.return_value = mock_job
        mock_repo.delete.return_value = True
        
        service = JobService(mock_repo)
        result = service.delete_job(1)
        
        assert result is True
        mock_repo.find_by_id.assert_called_once_with(1)
        mock_repo.delete.assert_called_once_with(1)
    
    def test_delete_job_not_found(self):
        mock_repo = Mock(spec=JobRepository)
        mock_repo.find_by_id.return_value = None
        
        service = JobService(mock_repo)
        result = service.delete_job(1)
        
        assert result is False
        mock_repo.delete.assert_not_called()
    
    def test_update_job_status_valid(self):
        mock_repo = Mock(spec=JobRepository)
        mock_job = Job(id=1, title="Test Job")
        mock_repo.find_by_id.return_value = mock_job
        
        service = JobService(mock_repo)
        status_fields = {"applied": True, "seen": True}
        result = service.update_job_status(1, status_fields)
        
        assert result is True
    
    def test_update_job_status_invalid_field(self):
        mock_repo = Mock(spec=JobRepository)
        mock_job = Job(id=1, title="Test Job")
        mock_repo.find_by_id.return_value = mock_job
        
        service = JobService(mock_repo)
        status_fields = {"invalid_field": True}
        
        with pytest.raises(ValueError, match="Invalid status field: invalid_field"):
            service.update_job_status(1, status_fields)