import unittest
from aiEnrichNew.jsonHelper import rawToJson, validateResult

class TestJsonHelper(unittest.TestCase):

    def test_rawToJson_valid(self):
        json_str = '{"key": "value"}'
        self.assertEqual(rawToJson(json_str), {"key": "value"})

    def test_rawToJson_with_markdown_ticks(self):
        json_str = '```json\n{"key": "value"}\n```'
        self.assertEqual(rawToJson(json_str), {"key": "value"})

    def test_rawToJson_with_thought(self):
        json_str = 'Thought: thinking...\n{"key": "value"}'
        self.assertEqual(rawToJson(json_str), {"key": "value"})

    def test_validateResult_removes_invalid_salary(self):
        result = {"salary": "Competitive"} # No numbers
        validateResult(result)
        self.assertIsNone(result["salary"])
    
    def test_validateResult_keeps_valid_salary(self):
        result = {"salary": "50000 EUR"} 
        validateResult(result)
        self.assertEqual(result["salary"], "50000 EUR")
    
    def test_listsToString(self):
        # Validate result implicitly calls listsToString
        result = {"required_technologies": ["java", "python"]}
        validateResult(result)
        self.assertEqual(result["required_technologies"], "java,python")

if __name__ == '__main__':
    unittest.main()
