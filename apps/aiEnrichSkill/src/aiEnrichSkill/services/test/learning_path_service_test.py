import pytest
from unittest.mock import MagicMock, patch

from ..idle_scheduler import LearningPathScheduler
from ..learning_path_service import MODULE, enrich_learning_paths, generate_learning_path_ollama


@pytest.fixture(autouse=True)
def inference_slot():
    with patch("aiEnrichSkill.services.learning_path_service.request_slot") as slot:
        slot.return_value.__enter__.return_value = True
        yield slot


@pytest.fixture
def repository():
    repo = MagicMock()
    repo.fetch_pending_learning_path_names.return_value = ["Python"]
    repo.has_pending_enrichment.return_value = False
    return repo


@patch("aiEnrichSkill.services.learning_path_service.parse_learning_path_result")
@patch("aiEnrichSkill.services.learning_path_service.query_ollama")
@patch("aiEnrichSkill.services.learning_path_service.build_learning_path_prompt_messages")
def test_generate_learning_path_ollama(mock_build, mock_query, mock_parse):
    mock_build.return_value = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"},
    ]
    mock_query.return_value = "Learning Path:\n- https://docs.python.org/"
    mock_parse.return_value = ["https://docs.python.org/"]
    assert generate_learning_path_ollama("Python", "Django") == ["https://docs.python.org/"]
    mock_query.assert_called_once()
    assert mock_query.call_args.kwargs["json_mode"] is False


@patch("aiEnrichSkill.services.learning_path_service.query_ollama", return_value=None)
@patch("aiEnrichSkill.services.learning_path_service.build_learning_path_prompt_messages")
def test_generate_learning_path_ollama_no_response(mock_build, _mock_query):
    mock_build.return_value = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    assert generate_learning_path_ollama("Python") == []


@patch("aiEnrichSkill.services.learning_path_service.collector")
@patch("aiEnrichSkill.services.learning_path_service.validate_learning_paths", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.fetch_skill_context_safe", return_value="context")
def test_enrich_learning_paths_success(_context, _generate, _validate, _collector, repository):
    assert enrich_learning_paths(repository, scheduler=LearningPathScheduler()) == 1
    repository.fetch_pending_learning_path_names.assert_called_once()
    repository.save_learning_path.assert_called_once_with("Python", ["https://docs.python.org/"])
    _collector.record_job.assert_called_once()
    assert _collector.record_job.call_args[0][0] == MODULE
    assert _collector.record_job.call_args[0][2] is True


@patch("aiEnrichSkill.services.learning_path_service.validate_learning_paths", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.fetch_skill_context_safe", return_value="")
def test_enrich_learning_paths_requests_the_low_priority_slot(_context, _generate, _validate, repository, inference_slot):
    enrich_learning_paths(repository, scheduler=LearningPathScheduler())
    assert inference_slot.call_args.kwargs["priority"] == "low"


def test_enrich_learning_paths_nothing_pending(repository):
    repository.fetch_pending_learning_path_names.return_value = []
    scheduler = LearningPathScheduler()
    scheduler.note_deferred("model_busy")
    assert enrich_learning_paths(repository, scheduler=scheduler) == 0
    assert scheduler.deferred is False
    repository.save_learning_path.assert_not_called()


@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama")
def test_enrich_learning_paths_yields_when_priority_work_appears(mock_generate, repository):
    repository.has_pending_enrichment.return_value = True
    assert enrich_learning_paths(repository, scheduler=LearningPathScheduler()) == 0
    mock_generate.assert_not_called()
    repository.save_learning_path.assert_not_called()


@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama")
def test_enrich_learning_paths_defers_when_the_model_is_busy(mock_generate, repository, inference_slot):
    inference_slot.return_value.__enter__.return_value = False
    scheduler = LearningPathScheduler()
    assert enrich_learning_paths(repository, scheduler=scheduler) == 0
    mock_generate.assert_not_called()
    assert scheduler.deferred is True


@patch("aiEnrichSkill.services.learning_path_service.collector")
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", side_effect=RuntimeError("model down"))
def test_enrich_learning_paths_records_failure_and_stops(_generate, mock_collector, repository):
    repository.fetch_pending_learning_path_names.return_value = ["Python", "Docker"]
    scheduler = LearningPathScheduler(max_failures=1)
    assert enrich_learning_paths(repository, scheduler=scheduler) == 0
    repository.save_learning_path.assert_not_called()
    mock_collector.record_job.assert_called_once()
    assert mock_collector.record_job.call_args[0][0] == MODULE
    assert mock_collector.record_job.call_args[0][2] is False
    mock_collector.record_error.assert_called_once_with(MODULE, "model down")
    assert scheduler.ready() is False


@patch("aiEnrichSkill.services.learning_path_service.collector")
@patch("aiEnrichSkill.services.learning_path_service.validate_learning_paths", return_value=[])
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", return_value=[])
def test_enrich_learning_paths_does_not_persist_empty_result(_generate, _validate, mock_collector, repository):
    scheduler = LearningPathScheduler()
    assert enrich_learning_paths(repository, scheduler=scheduler) == 0
    repository.save_learning_path.assert_not_called()
    assert mock_collector.record_job.call_args[0][2] is False
    assert scheduler.should_skip("Python") is True


@patch("aiEnrichSkill.services.learning_path_service.collector")
@patch("aiEnrichSkill.services.learning_path_service.validate_learning_paths", return_value=[])
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", return_value=["https://docs.python.org/"])
def test_enrich_learning_paths_runs_search_even_when_model_returns_no_usable_links(_generate, _validate, mock_collector, repository):
    scheduler = LearningPathScheduler()
    assert enrich_learning_paths(repository, scheduler=scheduler) == 0
    _validate.assert_called_once_with("Python", ["https://docs.python.org/"])
    repository.save_learning_path.assert_not_called()
    assert scheduler.should_skip("Python") is True


@pytest.mark.parametrize("names, expected_calls", [
    pytest.param(["Python", "Docker"], 2, id="batch_of_two"),
    pytest.param(["Python"], 1, id="single"),
], ids=lambda value: None)
@patch("aiEnrichSkill.services.learning_path_service.validate_learning_paths", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.fetch_skill_context_safe", return_value="")
def test_enrich_learning_paths_processes_each_pending_name(_context, mock_generate, _validate, repository, names, expected_calls):
    repository.fetch_pending_learning_path_names.return_value = names
    with patch("aiEnrichSkill.services.learning_path_service.get_learning_path_batch", return_value=expected_calls):
        assert enrich_learning_paths(repository, scheduler=LearningPathScheduler()) == expected_calls
    assert mock_generate.call_count == expected_calls
    assert repository.save_learning_path.call_count == expected_calls


@patch("aiEnrichSkill.services.learning_path_service.collector")
@patch("aiEnrichSkill.services.learning_path_service.validate_learning_paths", side_effect=[[], ["https://docs.python.org/"]])
@patch("aiEnrichSkill.services.learning_path_service.generate_learning_path_ollama", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.learning_path_service.fetch_skill_context_safe", return_value="")
def test_unverifiable_skill_rotates_to_next_candidate(_context, _generate, _validate, _collector, repository):
    repository.fetch_pending_learning_path_names.return_value = ["Galting", "Bicep"]
    scheduler = LearningPathScheduler(retry_seconds=900)
    assert enrich_learning_paths(repository, scheduler=scheduler) == 1
    repository.save_learning_path.assert_called_once_with("Bicep", ["https://docs.python.org/"])
    assert scheduler.should_skip("Galting") is True
    assert scheduler.ready() is True
