import json
from unittest.mock import MagicMock, patch
import pytest
from commonlib.repositories.skill_repository import DESCRIPTION_AND_PATH_UPDATE, DESCRIPTION_UPDATE, SkillRepository


@pytest.mark.parametrize("check_empty, has_description_filter", [
    pytest.param(True, True, id="empty_only"),
    pytest.param(False, False, id="all_pending"),
])
def test_fetch_pending_skill_names_query(check_empty, has_description_filter):
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Python",), ("Django",)]
    assert SkillRepository(mysql).fetch_pending_skill_names(5, check_empty) == ["Python", "Django"]
    query = mysql.fetchAll.call_args[0][0]
    assert "COALESCE(ai_enriched, 0) = 0" in query
    assert ("description IS NULL" in query) is has_description_filter


def test_fetch_pending_skill_names_empty():
    mysql = MagicMock()
    mysql.fetchAll.return_value = []
    assert SkillRepository(mysql).fetch_pending_skill_names(5) == []


@patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Django, Flask")
def test_fetch_skill_context_delegates(mock_context):
    mysql = MagicMock()
    assert SkillRepository(mysql).fetch_skill_context("Python") == "Django, Flask"
    mock_context.assert_called_once_with(mysql, "Python")


@pytest.mark.parametrize("learning_path, expected_query, include_json", [
    pytest.param([], DESCRIPTION_UPDATE, False, id="no_links"),
    pytest.param(["https://python.org"], DESCRIPTION_AND_PATH_UPDATE, True, id="with_links"),
])
def test_save_skill_result(learning_path, expected_query, include_json):
    mysql = MagicMock()
    SkillRepository(mysql).save_skill_result("Python", "Desc", "Cat", learning_path)
    query, args = mysql.executeAndCommit.call_args[0]
    assert query == expected_query
    assert args[0] == "Desc" and args[1] == "Cat" and args[-1] == "Python"
    assert (json.dumps(learning_path) in args) is include_json


def test_path_update_guards_curated_links():
    assert "CASE WHEN (learning_path IS NULL OR JSON_LENGTH(learning_path) = 0)" in DESCRIPTION_AND_PATH_UPDATE
    assert "ELSE learning_path END" in DESCRIPTION_AND_PATH_UPDATE
