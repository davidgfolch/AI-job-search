import json

import pytest
from structlog.testing import capture_logs
from unittest.mock import MagicMock, patch
from commonlib.skill_enricher_service import DESCRIPTION_AND_PATH_UPDATE, DESCRIPTION_UPDATE, process_skill_enrichment, parse_skill_llm_output


@pytest.mark.parametrize("limit", [10], ids=["default_limit"])
@patch("commonlib.sql.mysqlUtil.MysqlUtil")
@patch("commonlib.skill_enricher_service.get_skill_context")
def test_process_skill_enrichment_no_skills(mock_context, mock_mysql_cls, limit):
    mysql = MagicMock()
    mysql.fetchAll.return_value = []
    with capture_logs() as records:
        count = process_skill_enrichment(mysql, lambda n, c: "desc", limit=limit)
    assert count == 0
    skipped = [r for r in records if r["event"] == "jobs.skipped"]
    assert len(skipped) == 1
    assert skipped[0]["message"] == "No skills pending."
    assert skipped[0]["reason"] == "no_pending_skills"
    assert skipped[0]["limit"] == limit


@pytest.mark.parametrize("gen_result, expected_args, expected_query", [
    pytest.param(("Description", "Category"), ["Description", "Category", "Skill1"], DESCRIPTION_UPDATE, id="two_tuple_no_links"),
    pytest.param(("Description", "Category", []), ["Description", "Category", "Skill1"], DESCRIPTION_UPDATE, id="three_tuple_empty_links"),
    pytest.param(("Description", "Category", ["https://python.org"]), ["Description", "Category", json.dumps(["https://python.org"]), "Skill1"], DESCRIPTION_AND_PATH_UPDATE, id="three_tuple_with_links"),
    pytest.param("Just a description", ["Just a description", None, "Skill1"], DESCRIPTION_UPDATE, id="bare_string"),
], ids=lambda value: None)
def test_process_skill_enrichment_success(gen_result, expected_args, expected_query):
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=gen_result)
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 1
        gen_fn.assert_called_with("Skill1", "Context")
        mysql.executeAndCommit.assert_called_once()
        args = mysql.executeAndCommit.call_args[0]
        assert args[0] == expected_query
        assert args[1] == expected_args


def test_process_skill_enrichment_path_update_only_fills_empty_column():
    """Curated links win: the SQL must be guarded by IS NULL / JSON_LENGTH = 0."""
    assert "CASE WHEN (learning_path IS NULL OR JSON_LENGTH(learning_path) = 0)" in DESCRIPTION_AND_PATH_UPDATE
    assert "ELSE learning_path END" in DESCRIPTION_AND_PATH_UPDATE


def test_process_skill_enrichment_gen_fail():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=None)
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 0
        mysql.executeAndCommit.assert_not_called()


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
        assert "COALESCE(ai_enriched, 0) = 0" in call_args
        assert "description IS NULL" not in call_args


def test_process_skill_enrichment_null_ai_enriched_selected():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Fix Protocol",)]
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value=""):
        gen_fn = MagicMock(return_value=("Desc", "Other"))
        count = process_skill_enrichment(mysql, gen_fn)
        assert count == 1
        call_args = mysql.fetchAll.call_args[0][0]
        # NULL ai_enriched rows must be treated as pending (NULL = 0 never matches)
        assert "COALESCE(ai_enriched, 0) = 0" in call_args
        assert "description IS NULL" in call_args


@pytest.mark.parametrize("input_text, expected_desc_contains, expected_category, expected_links", [
    ("**Summary**: Python is a language.\n**Category**: Programming Language",
     "Python is a language", "Programming Language", []),
    ("Category: Cloud Platform\n\n**Summary**: GCP is a cloud platform.",
     "GCP is a cloud platform", "Cloud Platform", []),
    ("Just a description without category",
     "Just a description without category", "Other", []),
    ("", "", "Other", []),
    ("## Category: Framework\nDesc here",
     "Desc here", "Framework", []),
    ("**Category**: `DevOps`\nSome description",
     "Some description", "DevOps", []),
    ("**Summary**: Python.\n**Category**: Language\n**Learning Path**:\n- https://docs.python.org/3/\n- https://www.freecodecamp.org/",
     "Python", "Language", ["https://docs.python.org/3/", "https://www.freecodecamp.org/"]),
])
def test_parse_skill_llm_output(input_text, expected_desc_contains, expected_category, expected_links):
    desc, cat, links = parse_skill_llm_output(input_text)
    assert expected_desc_contains in desc
    assert cat == expected_category
    assert links == expected_links


def test_parse_skill_llm_output_strips_links_from_description():
    output = "**Summary**: Python is a language.\n**Learning Path**:\n- https://docs.python.org/\n**Category**: Language"
    desc, cat, links = parse_skill_llm_output(output)
    assert "https://" not in desc
    assert cat == "Language"
    assert links == ["https://docs.python.org/"]


def test_parse_skill_llm_output_learning_path_only():
    output = "Learning Path:\n- https://roadmap.sh/python\n- https://roadmap.sh/python/\n- https://roadmap.sh/python#intro"
    desc, cat, links = parse_skill_llm_output(output)
    assert desc == ""
    assert cat == "Other"
    assert links == ["https://roadmap.sh/python", "https://roadmap.sh/python#intro"]
