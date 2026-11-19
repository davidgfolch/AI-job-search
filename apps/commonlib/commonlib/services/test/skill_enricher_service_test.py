import pytest
from structlog.testing import capture_logs
from unittest.mock import MagicMock, patch
from commonlib.repositories.skill_repository import DESCRIPTION_AND_PATH_UPDATE, DESCRIPTION_UPDATE, SkillRepository
from commonlib.services.skill_enricher_service import BackendUnavailable, process_skill_enrichment


@pytest.mark.parametrize("limit", [10], ids=["default_limit"])
@patch("commonlib.repositories.skill_repository.get_skill_context")
def test_process_skill_enrichment_no_skills(mock_context, limit):
    mysql = MagicMock()
    mysql.fetchAll.return_value = []
    with capture_logs() as records:
        count = process_skill_enrichment(SkillRepository(mysql), lambda n, c: "desc", limit=limit)
    assert count == 0
    skipped = [r for r in records if r["event"] == "jobs.skipped"]
    assert len(skipped) == 1
    assert skipped[0]["message"] == "No skills pending."
    assert skipped[0]["reason"] == "no_pending_skills"
    assert skipped[0]["limit"] == limit


@pytest.mark.parametrize("gen_result, expected_args, expected_query", [
    pytest.param(("Description", "Category"), ["Description", "Category", "Skill1"], DESCRIPTION_UPDATE, id="two_tuple_no_links"),
    pytest.param(("Description", "Category", []), ["Description", "Category", "Skill1"], DESCRIPTION_UPDATE, id="three_tuple_empty_links"),
    pytest.param(("Description", "Category", ["https://python.org"]), ["Description", "Category", '[{"url": "https://python.org", "source": "unknown"}]', "Skill1"], DESCRIPTION_AND_PATH_UPDATE, id="three_tuple_with_links"),
    pytest.param(("Description", "Category", [{"url": "https://python.org", "source": "llm"}]), ["Description", "Category", '[{"url": "https://python.org", "source": "llm"}]', "Skill1"], DESCRIPTION_AND_PATH_UPDATE, id="three_tuple_with_source"),
    pytest.param("Just a description", ["Just a description", None, "Skill1"], DESCRIPTION_UPDATE, id="bare_string"),
], ids=lambda value: None)
def test_process_skill_enrichment_success(gen_result, expected_args, expected_query):
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=gen_result)
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
        assert count == 1
        gen_fn.assert_called_with("Skill1", "Context")
        mysql.executeAndCommit.assert_called_once()
        args = mysql.executeAndCommit.call_args[0]
        assert args[0] == expected_query
        assert args[1] == expected_args


def test_process_skill_enrichment_gen_fail():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=None)
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
        assert count == 0
        mysql.executeAndCommit.assert_not_called()


def test_process_skill_enrichment_invalid_result_format():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        count = process_skill_enrichment(SkillRepository(mysql), MagicMock(return_value=123))
        assert count == 0


def test_process_skill_enrichment_error_in_generation():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(side_effect=Exception("LLM error"))
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
        assert count == 0


def test_process_skill_enrichment_stops_the_batch_when_the_backend_goes_down():
    """Nothing is written when the server dies mid-batch: the remaining items stay pending for the next cycle."""
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",), ("Skill2",)]
    calls = []

    def gen_fn(name, _context):
        calls.append(name)
        raise BackendUnavailable(name)

    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
    assert calls == ["Skill1"]
    assert count == 0
    mysql.executeAndCommit.assert_not_called()


def test_process_skill_enrichment_error_in_context():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", side_effect=Exception("DB error")):
        gen_fn = MagicMock(return_value=("Desc", "Cat"))
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
        assert count == 1


def test_process_skill_enrichment_description_with_error():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=("Error: something went wrong", "Cat"))
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
        assert count == 0


def test_process_skill_enrichment_check_empty_false():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=("Desc", "Cat"))
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn, check_empty_description_only=False)
        assert count == 1
        query = mysql.fetchAll.call_args[0][0]
        assert "COALESCE(ai_enriched, 0) = 0" in query
        assert "description IS NULL" not in query


def test_process_skill_enrichment_null_ai_enriched_selected():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Fix Protocol",)]
    with patch("commonlib.repositories.skill_repository.get_skill_context", return_value=""):
        gen_fn = MagicMock(return_value=("Desc", "Other"))
        count = process_skill_enrichment(SkillRepository(mysql), gen_fn)
        assert count == 1
        query = mysql.fetchAll.call_args[0][0]
        assert "COALESCE(ai_enriched, 0) = 0" in query
        assert "description IS NULL" in query


def test_log_no_pending_skills():
    with capture_logs() as records:
        process_skill_enrichment(SkillRepository(MagicMock()), lambda n, c: "desc", limit=7)
    assert any(r["event"] == "jobs.skipped" for r in records)
