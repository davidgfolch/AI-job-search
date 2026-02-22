import unittest
from unittest.mock import MagicMock, patch, ANY
from ..job_enrichment_service import enrich_jobs, retry_failed_job

class TestJobEnrichmentService(unittest.TestCase):

    def setUp(self):
        self.repo = MagicMock()
        self.pipeline = MagicMock()

    @patch("aiEnrichNew.services.job_enrichment_service.process_batch")
    @patch("aiEnrichNew.services.job_enrichment_service._fetch_and_sort_jobs")
    def test_enrich_jobs_success(self, mock_fetch_sort, mock_process_batch):
        # Setup
        self.repo.count_pending_enrichment.return_value = 2
        self.repo.get_pending_enrichment_ids.return_value = [1, 2]
        mock_fetch_sort.return_value = [{"id": 1, "length": 10}, {"id": 2, "length": 20}]
        
        # Execute
        enrich_jobs(self.repo, self.pipeline, batch_size=2)
        
        # Verify
        mock_process_batch.assert_called_once()
        self.repo.get_pending_enrichment_ids.assert_called_once()
        mock_fetch_sort.assert_called_with(self.repo, [1, 2], sort_by_length=True)
        
    def test_enrich_jobs_no_pending(self):
        self.repo.count_pending_enrichment.return_value = 0
        
        count = enrich_jobs(self.repo, self.pipeline, batch_size=2)
        
        self.assertEqual(count, 0)
        self.pipeline.assert_not_called()

    @patch("aiEnrichNew.services.job_enrichment_service.process_batch")
    def test_retry_failed_job_found(self, mock_process_batch):
        self.repo.get_enrichment_error_id_retry.return_value = 1
        self.repo.get_job_to_retry.return_value = (1, "Title", "Company", "Markdown")
        
        result = retry_failed_job(self.repo, self.pipeline)
        
        self.assertEqual(result, 1)
        mock_process_batch.assert_called_once()
        self.repo.get_job_to_retry.assert_called_with(1)

    def test_retry_failed_job_none(self):
        self.repo.get_enrichment_error_id_retry.return_value = None
        
        result = retry_failed_job(self.repo, self.pipeline)
        
        self.assertEqual(result, 0)
        self.pipeline.assert_not_called()
