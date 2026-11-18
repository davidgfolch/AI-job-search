import pytest
from unittest.mock import patch, MagicMock

from commonlib.services.skill_enricher_service import BackendUnavailable
from ..enrichment_service import _enrich_ollama, enrich_skills, generate_skill_description_ollama
from .enrichment_service_fixtures import assert_failure_metric, make_ollama_mocks, run_enrich_ollama


@pytest.fixture(autouse=True)
def ollama_answers():
    """No test may probe a real Ollama server; individual tests override this with their own patch."""
    with patch("aiEnrichSkill.services.enrichment_service.ping_ollama", return_value=True):
        yield


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
    repository = MagicMock()
    result = enrich_skills(repository)
    assert result == expected
    if called_mock == "_enrich_ollama":
        mock_ollama.assert_called_once_with(repository, None)
        mock_hf.assert_not_called()
    elif called_mock == "_enrich_huggingface":
        mock_hf.assert_called_once_with(repository)
        mock_ollama.assert_not_called()
    else:
        mock_ollama.assert_not_called()
        mock_hf.assert_not_called()


@patch("aiEnrichSkill.services.enrichment_service.validate_learning_paths")
@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
@patch("aiEnrichSkill.services.enrichment_service.parse_skill_enrichment_result")
def test_generate_skill_description_ollama_success(mock_parse, mock_query, mock_build, mock_validate):
    make_ollama_mocks(mock_build, mock_query, mock_parse, "**Summary**: Python is a language. **Category**: Language", ("Python is a language", "Language", []))
    mock_validate.return_value = []
    result = generate_skill_description_ollama("Python", "Django")
    assert result == ("Python is a language", "Language", [])
    mock_query.assert_called_once()
    mock_validate.assert_called_once_with("Python", [])


@patch("aiEnrichSkill.services.enrichment_service.validate_learning_paths")
@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
@patch("aiEnrichSkill.services.enrichment_service.parse_skill_enrichment_result")
def test_generate_skill_description_ollama_validates_proposed_links(mock_parse, mock_query, mock_build, mock_validate):
    make_ollama_mocks(mock_build, mock_query, mock_parse, "raw", ("Python", "Language", ["https://python.org"]))
    mock_validate.return_value = ["https://python.org"]
    result = generate_skill_description_ollama("Python", "")
    assert result == ("Python", "Language", ["https://python.org"])
    mock_validate.assert_called_once_with("Python", ["https://python.org"])


@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
def test_generate_skill_description_ollama_failure(mock_query, mock_build):
    mock_build.return_value = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"}
    ]
    mock_query.return_value = None
    result = generate_skill_description_ollama("Python", "")
    assert result == ("", "Other", [])


@patch("aiEnrichSkill.services.enrichment_service.process_skill_enrichment", return_value=5)
@patch("aiEnrichSkill.services.enrichment_service.get_backend", return_value="ollama")
def test_enrich_ollama_delegates_to_shared_service(_mock_backend, mock_process):
    repository = MagicMock()
    assert enrich_skills(repository) == 5
    mock_process.assert_called_once()
    assert mock_process.call_args[0][0] is repository


@patch("aiEnrichSkill.services.enrichment_service.collector")
@patch("aiEnrichSkill.services.enrichment_service.validate_learning_paths")
@patch("aiEnrichSkill.services.enrichment_service.parse_skill_enrichment_result")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
def test_enrich_ollama_records_metric_on_success(mock_build, mock_query, mock_parse, mock_validate, mock_collector):
    make_ollama_mocks(mock_build, mock_query, mock_parse, "**Summary**: Python is a language. **Category**: Language", ("Python is a language", "Language", []))
    mock_validate.return_value = []
    result, generator_called = run_enrich_ollama()
    assert result == 1
    assert generator_called == [("Python is a language", "Language", [])]
    mock_collector.record_job.assert_called_once_with("aiEnrichSkill", mock_collector.record_job.call_args[0][1], True)


@patch("aiEnrichSkill.services.enrichment_service.collector")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
def test_enrich_ollama_records_metric_on_failure(mock_build, mock_query, mock_collector):
    make_ollama_mocks(mock_build, mock_query, query_result=None)
    run_enrich_ollama(name="Unknown", context="")
    assert_failure_metric(mock_collector)


@patch("aiEnrichSkill.services.enrichment_service.collector")
@patch("aiEnrichSkill.services.enrichment_service.process_skill_enrichment")
@patch("aiEnrichSkill.services.enrichment_service.ping_ollama", return_value=False)
def test_enrich_ollama_defers_the_cycle_when_ollama_is_down(mock_ping, mock_process, mock_collector):
    repository = MagicMock()
    repository.has_pending_enrichment.return_value = True
    assert _enrich_ollama(repository) == 0
    mock_process.assert_not_called()
    mock_collector.record_backend_unreachable.assert_called_once_with("aiEnrichSkill")


@patch("aiEnrichSkill.services.enrichment_service.process_skill_enrichment")
@pytest.mark.parametrize("pending", [True, False])
def test_enrich_ollama_does_not_probe_when_there_is_no_work(_mock_process, pending):
    repository = MagicMock()
    repository.has_pending_enrichment.return_value = pending
    with patch("aiEnrichSkill.services.enrichment_service.ping_ollama", return_value=True) as ping:
        _enrich_ollama(repository)
    assert ping.called is pending


@patch("aiEnrichSkill.services.enrichment_service.collector")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama", return_value=None)
@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
def test_unanswerable_skill_leaves_the_queue_when_ollama_is_up(mock_build, mock_query, _mock_collector):
    """Ollama answers but produced no description: retrying the same skill every cycle would block the queue."""
    repository = MagicMock()
    repository.has_pending_enrichment.return_value = True
    make_ollama_mocks(mock_build, mock_query, query_result=None)
    run_enrich_ollama(repository=repository)
    repository.skip_skill.assert_called_once_with("Python")


@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama", return_value=None)
@patch("aiEnrichSkill.services.enrichment_service.ping_ollama", side_effect=[True, False])
def test_backend_going_down_mid_batch_leaves_the_skill_pending(_mock_ping, mock_query, mock_build):
    """A server that died between the cycle probe and the request is waited for, never marked."""
    repository = MagicMock()
    repository.has_pending_enrichment.return_value = True
    make_ollama_mocks(mock_build, mock_query, query_result=None)
    with pytest.raises(BackendUnavailable):
        run_enrich_ollama(repository=repository)
    repository.skip_skill.assert_not_called()


@patch("aiEnrichSkill.services.enrichment_service.collector")
@patch("aiEnrichSkill.services.enrichment_service.query_ollama")
@patch("aiEnrichSkill.services.enrichment_service.build_skill_prompt_messages")
def test_enrich_ollama_records_metric_on_exception(mock_build, mock_query, mock_collector):
    make_ollama_mocks(mock_build, mock_query)
    mock_query.side_effect = RuntimeError("connection refused")
    run_enrich_ollama()
    assert_failure_metric(mock_collector)
    mock_collector.record_error.assert_called_once_with("aiEnrichSkill", "connection refused")
