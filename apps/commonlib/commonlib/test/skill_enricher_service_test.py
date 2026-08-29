import pytest
from unittest.mock import MagicMock, patch
from commonlib.skill_enricher_service import process_skill_enrichment, parse_skill_llm_output


@patch("commonlib.sql.mysqlUtil.MysqlUtil")
@patch("commonlib.skill_enricher_service.get_skill_context")
def test_process_skill_enrichment_no_skills(mock_context, mock_mysql_cls):
    mysql = MagicMock()
    mysql.fetchAll.return_value = []
    count = process_skill_enrichment(mysql, lambda n, c: "desc")
    assert count == 0


def test_process_skill_enrichment_success():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=("Description", "Category"))
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 1
        gen_fn.assert_called_with("Skill1", "Context")
        mysql.executeAndCommit.assert_called_once()
        args = mysql.executeAndCommit.call_args[0]
        assert args[1] == ["Description", "Category", "Skill1"]


def test_process_skill_enrichment_gen_fail():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=None)
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 0
        mysql.executeAndCommit.assert_not_called()


def test_process_skill_enrichment_string_result():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value="Just a description")
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 1


def test_process_skill_enrichment_invalid_result_format():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=123)
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 0


def test_process_skill_enrichment_error_in_generation():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(side_effect=Exception("LLM error"))
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 0


def test_process_skill_enrichment_error_in_context():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", side_effect=Exception("DB error")):
        gen_fn = MagicMock(return_value=("Desc", "Cat"))
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 1


def test_process_skill_enrichment_description_with_error():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=("Error: something went wrong", "Cat"))
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 0


def test_process_skill_enrichment_check_empty_false():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=("Desc", "Cat"))
        count = process_skill_enrichment(mysql, gen_fn, check_empty_description_only=False)
        assert count == 1
        call_args = mysql.fetchAll.call_args[0][0]
        assert "ai_enriched = 0" in call_args
        assert "description IS NULL" not in call_args


@pytest.mark.parametrize("input_text, expected_desc_contains, expected_category", [
    ("**Summary**: Python is a language.\n**Category**: Programming Language",
     "Python is a language", "Programming Language"),
    ("Category: Cloud Platform\n\n**Summary**: GCP is a cloud platform.",
     "GCP is a cloud platform", "Cloud Platform"),
    ("Just a description without category",
     "Just a description without category", "Other"),
    ("", "", "Other"),
    ("## Category: Framework\nDesc here",
     "Desc here", "Framework"),
    ("**Category**: `DevOps`\nSome description",
     "Some description", "DevOps"),
])
def test_parse_skill_llm_output(input_text, expected_desc_contains, expected_category):
    desc, cat = parse_skill_llm_output(input_text)
    assert expected_desc_contains in desc
    assert cat == expected_category
