import pytest
from unittest.mock import patch, MagicMock

from ..enrichment_service import enrich_skills, generate_skill_description_ollama


@pytest.mark.parametrize("backend, expected, called_mock", [
    pytest.param("ollama", 5, "_enrich_ollama", id="ollama_backend"),
    pytest.param("huggingface", 3, "_enrich_huggingface", id="huggingface_backend"),
    pytest.param("unknown", 0, None, id="unknown_backend"),
])
@patch("aiEnrichSkill.services.enrichment_service.get_backend")
@patch("aiEnrichSkill.services.enrichment_service._enrich_ollama")
@patch("aiEnrichSkill.services.enrichment_service._enrich_huggingface")
def test_enrich_skills(mock_hf, mock_ollama, mock_backend, backend, expected, called_mock):
    mock_backend.return_value = backend
    mock_ollama.return_value = 5
    mock_hf.return_value = 3
    mysql = MagicMock()

    result = enrich_skills(mysql)

    assert result == expected
    if called_mock == "_enrich_ollama":
        mock_ollama.assert_called_once_with(mysql)
        mock_hf.assert_not_called()
    elif called_mock == "_enrich_huggingface":
        mock_hf.assert_called_once_with(mysql)
        mock_ollama.assert_not_called()
    else:
        mock_ollama.assert_not_called()
        mock_hf.assert_not_called()


@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
@patch("aiEnrichSkill.services.enrichment_service.parse_skill_enrichment_result")
def test_generate_skill_description_ollama_success(mock_parse, mock_query, mock_build):
    mock_build.return_value = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "user prompt"}
    ]
    mock_query.return_value = "**Summary**: Python is a language. **Category**: Language"
    mock_parse.return_value = ("Python is a language", "Language")

    result = generate_skill_description_ollama("Python", "Django")
    assert result == ("Python is a language", "Language")
    mock_query.assert_called_once()


@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
def test_generate_skill_description_ollama_failure(mock_query, mock_build):
    mock_build.return_value = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"}
    ]
    mock_query.return_value = None

    result = generate_skill_description_ollama("Python", "")
    assert result == ("", "Other")


@patch("aiEnrichSkill.services.enrichment_service.get_backend")
@patch("aiEnrichSkill.services.enrichment_service.MysqlUtil")
@patch("aiEnrichSkill.services.enrichment_service.process_skill_enrichment")
def test_enrich_ollama_delegates_to_commonlib(mock_process, mock_mysql_cls, mock_backend):
    mock_backend.return_value = "ollama"
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_process.return_value = 5

    result = enrich_skills(mysql)
    assert result == 5


@patch("aiEnrichSkill.services.enrichment_service.get_backend")
@patch("aiEnrichSkill.services.enrichment_service._fetch_pending_skills")
@patch("aiEnrichSkill.llm_client.get_pipeline")
@patch("aiEnrichSkill.services.enrichment_service._process_skill_batch")
def test_enrich_huggingface(mock_process_batch, mock_pipeline, mock_fetch, mock_backend):
    mock_backend.return_value = "huggingface"
    mysql = MagicMock()
    mock_fetch.return_value = [{"name": "Python"}, {"name": "Docker"}]
    mock_pipeline.return_value = MagicMock()
    mock_process_batch.return_value = 2

    result = enrich_skills(mysql)
    assert result == 2


@patch("aiEnrichSkill.services.enrichment_service.get_backend")
@patch("aiEnrichSkill.services.enrichment_service._fetch_pending_skills")
def test_enrich_huggingface_no_skills(mock_fetch, mock_backend):
    mock_backend.return_value = "huggingface"
    mysql = MagicMock()
    mock_fetch.return_value = []

    result = enrich_skills(mysql)
    assert result == 0
