import unittest
from unittest.mock import MagicMock, patch
from aiEnrichNew.jsonHelper import rawToJson, validateResult, saveError, listsToString

class TestJsonHelper(unittest.TestCase):

    def test_rawToJson_basic(self):
        js = '{"a": 1}'
        self.assertEqual(rawToJson(js), {"a": 1})

    def test_rawToJson_fixes(self):
        raw_bs = r"""```json
        {"text": "a"}"""
        self.assertEqual(rawToJson(raw_bs), {"text": r"a"})
        raw_bs = r'```json{"text": "a"}'
        self.assertEqual(rawToJson(raw_bs), {"text": r"a"})
        raw_bs = r'```{"text": "a"}'
        self.assertEqual(rawToJson(raw_bs), {"text": r"a"})

    def test_rawToJson_exception(self):
        # Unfixable JSON -> Should raise exception and print error
        raw = '{"key": }'
        with self.assertRaises(Exception):
            rawToJson(raw)

    def test_validateResult_salary(self):
        # Numeric salary
        res = {"salary": "50000"}
        validateResult(res)
        self.assertEqual(res["salary"], "50000")

        # No numbers -> None
        res2 = {"salary": "Competitive Salary"}
        validateResult(res2)
        self.assertIsNone(res2["salary"])

        # "Sueldo: 30k" -> "30k"
        res3 = {"salary": "Sueldo: 30000"}
        validateResult(res3)
        self.assertEqual(res3["salary"].strip(), "30000")

    def test_validateResult_cv_match(self):
        # Valid
        res = {"cv_match_percentage": "80"}
        validateResult(res)
        
        # Invalid numeric
        res2 = {"cv_match_percentage": "150"}
        validateResult(res2)
        self.assertIsNone(res2["cv_match_percentage"])

        # Invalid format
        res3 = {"cv_match_percentage": "high"}
        validateResult(res3)
        self.assertIsNone(res3["cv_match_percentage"])

    def test_listsToString(self):
        res = {
            "tech": ["python", "java"],
            "other": "git"
        }
        listsToString(res, ["tech", "other"])
        self.assertEqual(res["tech"], "python,java")
        self.assertEqual(res["other"], "git")

    @patch('aiEnrichNew.jsonHelper.updateFieldsQuery')
    def test_saveError(self, mock_query_builder):
        mock_mysql = MagicMock()
        mock_mysql.executeAndCommit.return_value = 1
        mock_query_builder.return_value = ("SQL", ("params",))
        
        errors = set()
        saveError(mock_mysql, errors, 10, "Title", "Comp", Exception("Oops"), True)
        
        self.assertEqual(len(errors), 1)
        mock_query_builder.assert_called()
        # verify args to query builder have ai_enrich_error and ai_enriched=True
        args, _ = mock_query_builder.call_args
        self.assertEqual(args[0], [10])
        self.assertIn('ai_enrich_error', args[1])
        self.assertTrue(args[1]['ai_enriched'])

        # Test for cv match error (dataExtractor=False)
        saveError(mock_mysql, errors, 11, "T", "C", Exception("E"), False)
        args, _ = mock_query_builder.call_args
        self.assertEqual(args[1], {'cv_match_percentage': -1})

if __name__ == '__main__':
    unittest.main()
