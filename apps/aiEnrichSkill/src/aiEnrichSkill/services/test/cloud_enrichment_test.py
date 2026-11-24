from unittest.mock import MagicMock, patch

import pytest

from .. import cloud_enrichment
from ..cloud_enrichment import _enrich_cloud, generate_skill_description_cloud


@patch("aiEnrichSkill.services.cloud_enrichment.validate_learning_paths", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.cloud_enrichment.parse_skill_enrichment_result", return_value=("Python", "Language", ["https://docs.python.org/"]))
@patch("aiEnrichSkill.services.cloud_enrichment.build_skill_prompt_messages", return_value=[{"role": "user", "content": "Skill: Python"}])
@patch("aiEnrichSkill.services.cloud_enrichment.get_timeout", return_value=30)
@patch("aiEnrichSkill.services.cloud_enrichment.get_backend", return_value="gemini")
@patch("aiEnrichSkill.services.cloud_enrichment.chat", return_value="**Summary**: Python")
def test_generate_skill_description_cloud(mock_chat, _backend, _timeout, _build, _parse, mock_validate):
    assert generate_skill_description_cloud("Python", "Django") == ("Python", "Language", ["https://docs.python.org/"])
    assert mock_chat.call_args.args[0] == "gemini"
    assert mock_chat.call_args.kwargs["timeout"] == 30
    mock_validate.assert_called_once_with("Python", ["https://docs.python.org/"])


@patch("aiEnrichSkill.services.cloud_enrichment.chat", return_value=None)
def test_generate_skill_description_cloud_without_answer(mock_chat):
    assert generate_skill_description_cloud("Python") == ("", "Other", [])
    mock_chat.assert_called_once()


@patch("aiEnrichSkill.services.cloud_enrichment.ping", return_value=False)
@patch("aiEnrichSkill.services.cloud_enrichment.collector")
@patch("aiEnrichSkill.services.cloud_enrichment.get_backend", return_value="groq")
def test_enrich_cloud_defers_when_provider_is_down(mock_backend, mock_collector, _ping):
    repository = MagicMock()
    repository.has_pending_enrichment.return_value = True
    assert _enrich_cloud(repository) == 0
    mock_collector.record_backend_unreachable.assert_called_once_with("aiEnrichSkill")
    mock_backend.assert_called()


@pytest.mark.parametrize("description,expected", [
    ("Python", True),
    ("", False),
])
@patch("aiEnrichSkill.services.cloud_enrichment.ping", return_value=True)
@patch("aiEnrichSkill.services.cloud_enrichment.collector")
@patch("aiEnrichSkill.services.cloud_enrichment.get_enrich_limit", return_value=10)
@patch("aiEnrichSkill.services.cloud_enrichment.get_backend", return_value="groq")
def test_enrich_cloud_records_result(mock_backend, _limit, mock_collector, _ping, description, expected):
    repository = MagicMock()
    repository.has_pending_enrichment.return_value = False
    with patch.object(cloud_enrichment, "generate_skill_description_cloud", return_value=(description, "Other", [])), \
         patch.object(cloud_enrichment, "process_skill_enrichment", side_effect=lambda repo, gen, **kwargs: gen("Python", "")):
        result = _enrich_cloud(repository)
    assert result == (description, "Other", [])
    assert mock_collector.record_job.call_args[0][2] is expected
    mock_backend.assert_called()
