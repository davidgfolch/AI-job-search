from unittest.mock import patch, MagicMock
import pytest
from aiEnrich3.dataExtractor import dataExtractor

@pytest.fixture
def mock_dependencies():
    with patch("aiEnrich3.dataExtractor.MysqlUtil") as mock_mysql_util, \
         patch("aiEnrich3.dataExtractor.AiEnrichRepository") as mock_repo_class, \
         patch("aiEnrich3.dataExtractor.ExtractionPipeline") as mock_pipeline_class, \
         patch("aiEnrich3.dataExtractor.get_batch_size") as mock_get_batch_size, \
         patch("aiEnrich3.dataExtractor.enrich_jobs") as mock_enrich_jobs, \
         patch("aiEnrich3.dataExtractor.retry_failed_job") as mock_retry_failed_job:
        
        mock_mysql = MagicMock()
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline_instance
        
        mock_get_batch_size.return_value = 4
        
        yield {
            "mysql_util": mock_mysql_util,
            "repo_class": mock_repo_class,
            "repo": mock_repo,
            "pipeline_class": mock_pipeline_class,
            "pipeline_instance": mock_pipeline_instance,
            "get_batch_size": mock_get_batch_size,
            "enrich_jobs": mock_enrich_jobs,
            "retry_failed_job": mock_retry_failed_job,
        }

@pytest.mark.parametrize("total_pending, error_id, initial_pipeline, expected_processed", [
    (0, None, None, 0),         # Scenario 1: No pending, no error, no pipeline
    (1, None, None, 10),        # Scenario 2: Pending, no error, no pipeline (creates pipeline)
    (0, 123, None, 5),          # Scenario 3: No pending, error, no pipeline (creates pipeline)
    (2, 456, "existing_pipe", 15) # Scenario 4: Pending, error, existing pipeline
])
def test_dataExtractor(total_pending, error_id, initial_pipeline, expected_processed, mock_dependencies):
    deps = mock_dependencies
    deps["repo"].count_pending_enrichment.return_value = total_pending
    deps["repo"].get_enrichment_error_id_retry.return_value = error_id
    
    # Setup returns
    deps["retry_failed_job"].return_value = 5 if error_id is not None else 0
    deps["enrich_jobs"].return_value = 10 if total_pending > 0 else 0
    
    pipeline_arg = deps["pipeline_instance"] if initial_pipeline == "existing_pipe" else None
    
    processed, returned_pipeline = dataExtractor(pipeline_arg)
    
    assert processed == expected_processed
    if total_pending == 0 and error_id is None:
        assert returned_pipeline is None
    else:
        assert returned_pipeline is not None
        if initial_pipeline is None:
            deps["pipeline_class"].assert_called_once()
        else:
            deps["pipeline_class"].assert_not_called()
