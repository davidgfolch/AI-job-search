
import unittest
from unittest.mock import MagicMock
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context

class TestSkillContext(unittest.TestCase):
    def test_get_skill_context_parsing(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        
        # Mock fetchAll to return various formats of tech lists
        mock_mysql.fetchAll.return_value = [
            ("['Python', 'Django']", "['Redis', 'Celery']"), # JSON-like
            ("Java, Spring Boot", "Kafka, Docker"),          # Comma-separated
            (None, "['React']"),                             # Missing required
            ("['Terraform']", None),                         # Missing optional
            ("['Python']", "")                               # Empty string
        ]
        
        skill_name = "Python"
        context = get_skill_context(mock_mysql, skill_name)
        
        # Check that 'Python' is excluded
        self.assertNotIn("Python", context)
        
        # Check that other techs are present
        expected_techs = ["Django", "Redis", "Celery", "Java", "Spring Boot", "Kafka", "Docker", "React", "Terraform"]
        for tech in expected_techs:
            self.assertIn(tech, context)
            
    def test_get_skill_context_empty(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = []
        
        context = get_skill_context(mock_mysql, "Anything")
        self.assertEqual(context, "")

if __name__ == '__main__':
    unittest.main()
