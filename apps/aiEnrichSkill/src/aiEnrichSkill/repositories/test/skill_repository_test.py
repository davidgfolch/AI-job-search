import json
from unittest.mock import MagicMock, patch

import pytest

from ..skill_repository import PENDING_LEARNING_PATH_QUERY, UPDATE_LEARNING_PATH_QUERY, SkillRepository


def test_fetch_pending_skill_names_treats_null_ai_enriched_as_pending():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Fix Protocol",)]
    assert SkillRepository(mysql).fetch_pending_skill_names(10) == ["Fix Protocol"]
    query, params = mysql.fetchAll.call_args[0]
    # NULL ai_enriched never matches `ai_enriched = 0`, so COALESCE is required
    assert "COALESCE(ai_enriched, 0) = 0" in query
    assert "description" not in query
    assert params == (10,)


def test_fetch_pending_skill_names_filters_empty_descriptions():
    mysql = MagicMock()
    mysql.fetchAll.return_value = None
    assert SkillRepository(mysql).fetch_pending_skill_names(5, empty_description_only=True) == []
    query = mysql.fetchAll.call_args[0][0]
    assert "COALESCE(ai_enriched, 0) = 0" in query
    assert "description IS NULL OR description = ''" in query


def test_fetch_pending_learning_path_names_uses_empty_only_query():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Python",), ("Docker",)]
    repository = SkillRepository(mysql)
    assert repository.fetch_pending_learning_path_names(2) == ["Python", "Docker"]
    args = mysql.fetchAll.call_args[0]
    assert args[0] == PENDING_LEARNING_PATH_QUERY
    assert args[1] == (2,)
    assert "ai_enriched = 1" in PENDING_LEARNING_PATH_QUERY
    assert "JSON_LENGTH(learning_path) = 0" in PENDING_LEARNING_PATH_QUERY
    assert "ORDER BY disabled ASC, name ASC" in PENDING_LEARNING_PATH_QUERY


def test_has_pending_enrichment():
    mysql = MagicMock()
    mysql.fetchAll.side_effect = [[("Python",)], []]
    repository = SkillRepository(mysql)
    assert repository.has_pending_enrichment() is True
    assert repository.has_pending_enrichment() is False
    query = mysql.fetchAll.call_args[0][0]
    # Must match the tier-1 eligibility filter, or a curated skill blocks the backfill forever.
    assert "COALESCE(ai_enriched, 0) = 0" in query
    assert "description IS NULL OR description = ''" in query


def test_save_learning_path_serializes_json_and_guards_curated_links():
    mysql = MagicMock()
    SkillRepository(mysql).save_learning_path("Python", ["https://docs.python.org/"])
    args = mysql.executeAndCommit.call_args[0]
    assert args[0] == UPDATE_LEARNING_PATH_QUERY
    assert args[1] == [json.dumps(["https://docs.python.org/"]), "Python"]
    assert "JSON_LENGTH(learning_path) = 0" in UPDATE_LEARNING_PATH_QUERY


@pytest.mark.parametrize("learning_path, expected_args, has_learning_path_field", [
    pytest.param([], ["Desc", "Cat", "Python"], False, id="no_links"),
    pytest.param(["https://python.org"], ["Desc", "Cat", json.dumps(["https://python.org"]), "Python"], True, id="with_links"),
])
def test_save_skill_result(learning_path, expected_args, has_learning_path_field):
    mysql = MagicMock()
    SkillRepository(mysql).save_skill_result("Python", "Desc", "Cat", learning_path)
    args = mysql.executeAndCommit.call_args[0]
    assert args[1] == expected_args
    assert ("learning_path" in args[0]) is has_learning_path_field


@patch("aiEnrichSkill.repositories.skill_repository.process_skill_enrichment", return_value=3)
def test_run_pending_enrichment_delegates_to_shared_loop(mock_process):
    mysql = MagicMock()
    generate = MagicMock()
    assert SkillRepository(mysql).run_pending_enrichment(generate, limit=4, check_empty_description_only=False) == 3
    mock_process.assert_called_once_with(mysql, generate, limit=4, check_empty_description_only=False)


@patch("aiEnrichSkill.repositories.skill_repository.get_skill_context", return_value="Django, Flask")
def test_fetch_skill_context_delegates_to_commonlib(mock_context):
    mysql = MagicMock()
    assert SkillRepository(mysql).fetch_skill_context("Python") == "Django, Flask"
    mock_context.assert_called_once_with(mysql, "Python")
