import pytest
from unittest.mock import patch, MagicMock
from aiEnrichNew.dataExtractor import dataExtractor, retry_failed_jobs

@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.get_pipeline")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
@patch("aiEnrichNew.dataExtractor.enrich_jobs")
def test_dataExtractor_calls_service(mock_enrich_jobs, mock_repo_cls, mock_pipe_fac, mock_mysql):
    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.count_pending_enrichment.return_value = 5 # Should be > 0
    
    pipe = MagicMock()
    mock_pipe_fac.return_value = pipe
    
    dataExtractor()
    
    assert mock_enrich_jobs.called
    args, _ = mock_enrich_jobs.call_args
    assert args[0] == repo
    assert args[1] == pipe


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.get_pipeline")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
@patch("aiEnrichNew.dataExtractor.retry_failed_job")
def test_retry_calls_service(mock_retry, mock_repo_cls, mock_pipe_fac, mock_mysql):
    retry_failed_jobs()
    assert mock_retry.called
