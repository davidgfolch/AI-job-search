import unittest
from unittest.mock import patch
from ..parsers import parse_job_enrichment_result, parse_skill_enrichment_result

class TestParsers(unittest.TestCase):

    @patch("aiEnrichNew.domain.parsers.rawToJson")
    @patch("aiEnrichNew.domain.parsers.validateResult")
    def test_parse_job_enrichment_result_success(self, mock_validate, mock_rawToJson):
        mock_rawToJson.return_value = {"key": "value"}
        
        result = parse_job_enrichment_result("some json")
        
        self.assertEqual(result, {"key": "value"})
        mock_validate.assert_called_with({"key": "value"})

    @patch("aiEnrichNew.domain.parsers.rawToJson")
    def test_parse_job_enrichment_result_none(self, mock_rawToJson):
        mock_rawToJson.return_value = None
        
        result = parse_job_enrichment_result("invalid json")
        
        self.assertIsNone(result)

    @patch("aiEnrichNew.domain.parsers.rawToJson")
    @patch("aiEnrichNew.domain.parsers.validateResult")
    def test_parse_job_enrichment_result_exception(self, mock_validate, mock_rawToJson):
        mock_rawToJson.side_effect = Exception("Parsing error")
        
        with self.assertRaises(Exception):
            parse_job_enrichment_result("bad content")

    @patch("aiEnrichNew.domain.parsers.parse_skill_output_helper")
    def test_parse_skill_enrichment_result(self, mock_helper):
        mock_helper.return_value = ("Description", "Category")
        
        result = parse_skill_enrichment_result('"Some content"')
        
        self.assertEqual(result, ("Description", "Category"))
        # Verify stripping
        mock_helper.assert_called_with("Some content")
