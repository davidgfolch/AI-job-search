
import unittest
from unittest.mock import MagicMock
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context


class TestSkillContext(unittest.TestCase):
    def test_get_skill_context_parsing(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = [
            ("['Python', 'Django']", "['Redis', 'Celery']"),
            ("Java, Spring Boot", "Kafka, Docker"),
            (None, "['React']"),
            ("['Terraform']", None),
            ("['Python']", "")
        ]
        skill_name = "Python"
        context = get_skill_context(mock_mysql, skill_name)
        self.assertNotIn("Python", context)
        expected_techs = ["Django", "Redis", "Celery", "Java", "Spring Boot", "Kafka", "Docker", "React", "Terraform"]
        for tech in expected_techs:
            self.assertIn(tech, context)

    def test_get_skill_context_empty(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = []
        context = get_skill_context(mock_mysql, "Anything")
        self.assertEqual(context, "")

    def test_get_skill_context_invalid_json_fallback_to_comma(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = [
            ("not-a-valid-json", None),
        ]
        context = get_skill_context(mock_mysql, "test")
        self.assertIn("not-a-valid-json", context)

    def test_get_skill_context_non_list_json(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = [
            ('"just a string"', None),
        ]
        context = get_skill_context(mock_mysql, "test")
        self.assertIn("just a string", context)

    def test_get_skill_context_sorted_limit_30(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        techs = [f"Tech{i}" for i in range(40)]
        mock_mysql.fetchAll.return_value = [
            (", ".join(techs), None),
        ]
        context = get_skill_context(mock_mysql, "X")
        items = [t.strip() for t in context.split(", ")]
        self.assertLessEqual(len(items), 30)

    def test_get_skill_context_comma_fallback(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = [
            ("React, Angular, Vue", None),
        ]
        context = get_skill_context(mock_mysql, "X")
        self.assertIn("React", context)
        self.assertIn("Angular", context)
        self.assertIn("Vue", context)

    def test_get_skill_context_both_columns(self):
        mock_mysql = MagicMock(spec=MysqlUtil)
        mock_mysql.fetchAll.return_value = [
            ("Python", "Django"),
        ]
        context = get_skill_context(mock_mysql, "X")
        self.assertIn("Python", context)
        self.assertIn("Django", context)


if __name__ == '__main__':
    unittest.main()
