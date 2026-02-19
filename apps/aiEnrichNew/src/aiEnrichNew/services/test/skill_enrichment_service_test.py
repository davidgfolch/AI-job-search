import unittest
from unittest.mock import MagicMock, patch, ANY
from ..skill_enrichment_service import enrich_skills

class TestSkillEnrichmentService(unittest.TestCase):

    def setUp(self):
        self.mysql = MagicMock()
        self.pipeline = MagicMock()

    @patch("aiEnrichNew.services.skill_enrichment_service.process_batch")
    @patch("aiEnrichNew.services.skill_enrichment_service._fetch_pending_skills")
    @patch("aiEnrichNew.services.skill_enrichment_service.getEnvBool")
    @patch("aiEnrichNew.services.skill_enrichment_service.get_batch_size")
    def test_enrich_skills_success(self, mock_batch_size, mock_env_bool, mock_fetch, mock_process_batch):
        # Setup
        mock_env_bool.return_value = True
        mock_batch_size.return_value = 10
        mock_fetch.return_value = [{"name": "Python"}, {"name": "Java"}]
        mock_process_batch.return_value = 2 # simulate success count return from process_batch helper inside service
        
        # Need to mock the return of _process_skill_batch_pipeline or ensure it uses process_batch
        # In this case I am mocking process_batch, but enrich_skills calls _process_skill_batch_pipeline
        # which calls process_batch.
        # However, _process_skill_batch_pipeline returns success_count which comes from the side effects of on_success
        # passed to process_batch.
        
        # To strictly test the orchestration in enrich_skills without complex side effects setup,
        # we can patch _process_skill_batch_pipeline.
        with patch("aiEnrichNew.services.skill_enrichment_service._process_skill_batch_pipeline") as mock_pipeline_runner:
            mock_pipeline_runner.return_value = 2
            
            count = enrich_skills(self.mysql, self.pipeline)
            
            self.assertEqual(count, 2)
            mock_fetch.assert_called()
            mock_pipeline_runner.assert_called()

    @patch("aiEnrichNew.services.skill_enrichment_service.getEnvBool")
    def test_enrich_skills_disabled(self, mock_env_bool):
        mock_env_bool.return_value = False
        
        count = enrich_skills(self.mysql, self.pipeline)
        
        self.assertEqual(count, 0)
        self.mysql.fetchAll.assert_not_called()

    @patch("aiEnrichNew.services.skill_enrichment_service.process_batch")
    @patch("aiEnrichNew.services.skill_enrichment_service._fetch_pending_skills")
    @patch("aiEnrichNew.services.skill_enrichment_service.getEnvBool")
    def test_enrich_skills_no_pending(self, mock_env_bool, mock_fetch, mock_process_batch):
        mock_env_bool.return_value = True
        mock_fetch.return_value = []
        
        count = enrich_skills(self.mysql, self.pipeline)
        
        self.assertEqual(count, 0)
        mock_process_batch.assert_not_called()
