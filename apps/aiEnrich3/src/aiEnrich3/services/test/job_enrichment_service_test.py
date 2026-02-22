import pytest
from unittest.mock import MagicMock, patch
from aiEnrich3.services.job_enrichment_service import (
    _save_job_result,
    _update_error_state,
    enrich_jobs,
    retry_failed_job,
    _fetch_and_sort_jobs,
    _process_job_batch_local,
)

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def mock_pipeline():
    return MagicMock()

def test_save_job_result(mock_repo):
    result = {
        'salary': '100k',
        'required_skills': ['Python', 'Docker'],
        'optional_skills': ['AWS'],
        'modality': 'REMOTE'
    }
    _save_job_result(mock_repo, 1, "test_company", result)
    mock_repo.update_enrichment.assert_called_once_with(
        id=1,
        salary='100k',
        required_tech='Python, Docker',
        optional_tech='AWS',
        modality='REMOTE'
    )

def test_save_job_result_empty(mock_repo):
    result = {}
    _save_job_result(mock_repo, 2, "test_company", result)
    mock_repo.update_enrichment.assert_called_once_with(
        id=2,
        salary=None,
        required_tech=None,
        optional_tech=None,
        modality=None
    )

def test_update_error_state_success(mock_repo):
    mock_repo.update_enrichment_error.return_value = 1
    _update_error_state(mock_repo, 1, "Some error", True)
    mock_repo.update_enrichment_error.assert_called_once_with(1, "Some error", True)

def test_update_error_state_fail(mock_repo):
    mock_repo.update_enrichment_error.return_value = 0
    _update_error_state(mock_repo, 1, "Some error", True)
    mock_repo.update_enrichment_error.assert_called_once_with(1, "Some error", True)

@patch('aiEnrich3.services.job_enrichment_service._fetch_and_sort_jobs')
@patch('aiEnrich3.services.job_enrichment_service._process_job_batch_local')
def test_enrich_jobs(mock_process, mock_fetch, mock_repo, mock_pipeline):
    mock_repo.count_pending_enrichment.return_value = 2
    mock_repo.get_pending_enrichment_ids.return_value = [1, 2]
    mock_fetch.return_value = [{'id': 1}, {'id': 2}]
    
    total = enrich_jobs(mock_repo, mock_pipeline, 1)
    
    assert total == 2
    assert mock_process.call_count == 2
    
def test_enrich_jobs_empty(mock_repo, mock_pipeline):
    mock_repo.count_pending_enrichment.return_value = 0
    total = enrich_jobs(mock_repo, mock_pipeline, 1)
    assert total == 0

@patch('aiEnrich3.services.job_enrichment_service._process_job_batch_local')
def test_retry_failed_job_success(mock_process, mock_repo, mock_pipeline):
    mock_repo.get_enrichment_error_id_retry.return_value = 1
    mock_repo.get_job_to_retry.return_value = (1, "Title", b"markdown bytes", "Company")
    
    res = retry_failed_job(mock_repo, mock_pipeline)
    assert res == 1
    mock_process.assert_called_once()
    
def test_retry_failed_job_empty(mock_repo, mock_pipeline):
    mock_repo.get_enrichment_error_id_retry.return_value = None
    res = retry_failed_job(mock_repo, mock_pipeline)
    assert res == 0

def test_retry_failed_job_not_found(mock_repo, mock_pipeline):
    mock_repo.get_enrichment_error_id_retry.return_value = 1
    mock_repo.get_job_to_retry.return_value = None
    res = retry_failed_job(mock_repo, mock_pipeline)
    assert res == 0

@patch('aiEnrich3.services.job_enrichment_service.get_input_max_len')
def test_fetch_and_sort_jobs(mock_max_len, mock_repo):
    mock_max_len.return_value = 100
    mock_repo.get_job_to_enrich.side_effect = [
        (1, "Title 1", b"markdown chars", "Company 1"),
        (2, "Title 2", "string markdown "*20, "Company 2"),
        Exception("DB Error"),
        (4, "Title 4", None, "Company 4")
    ]
    
    res = _fetch_and_sort_jobs(mock_repo, [1, 2, 3, 4], sort_by_length=True)
    
    assert len(res) == 3
    # Sorted by length: 4 (0), 1 (14), 2 (100 truncated)
    assert res[0]['id'] == 4
    assert res[0]['length'] == 0
    assert res[1]['id'] == 1
    assert res[1]['length'] == 14
    assert res[2]['id'] == 2
    assert res[2]['length'] == 100

@patch('aiEnrich3.services.job_enrichment_service._save_job_result')
@patch('aiEnrich3.services.job_enrichment_service._update_error_state')
@patch('aiEnrich3.services.job_enrichment_service.printJob')
@patch('aiEnrich3.services.job_enrichment_service.footer')
@patch('aiEnrich3.services.job_enrichment_service.StopWatch')
def test_process_job_batch_local_success(mock_sw, mock_footer, mock_printJob, mock_update_err, mock_save, mock_repo, mock_pipeline):
    batch = [{'id': 1, 'title': 'T', 'company': 'C', 'markdown': 'text', 'length': 4}]
    errors = set()
    mock_pipeline.process_job.return_value = {"salary": "100k"}
    
    _process_job_batch_local(mock_repo, mock_pipeline, batch, 1, 0, "test", 0.0, 0, errors)
    
    mock_pipeline.process_job.assert_called_once_with('text')
    mock_save.assert_called_once()
    mock_printJob.assert_called_once()
    mock_footer.assert_called_once()
    mock_update_err.assert_not_called()
    assert len(errors) == 0

@patch('aiEnrich3.services.job_enrichment_service._save_job_result')
@patch('aiEnrich3.services.job_enrichment_service._update_error_state')
@patch('aiEnrich3.services.job_enrichment_service.StopWatch')
def test_process_job_batch_local_error(mock_sw, mock_update_err, mock_save, mock_repo, mock_pipeline):
    batch = [{'id': 1, 'title': 'T', 'company': 'C', 'markdown': 'text', 'length': 4}]
    errors = set()
    mock_pipeline.process_job.side_effect = Exception("Pipeline error")
    
    _process_job_batch_local(mock_repo, mock_pipeline, batch, 1, 0, "retry", 0.0, 0, errors)
    
    mock_save.assert_not_called()
    mock_update_err.assert_called_once()
    assert len(errors) == 1
