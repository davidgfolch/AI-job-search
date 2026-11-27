from structlog.testing import capture_logs
from unittest.mock import patch, MagicMock

from ..hf_enrichment import _enrich_huggingface
from .enrichment_service_fixtures import assert_failure_metric, run_process_skill_batch


def _make_repository(names):
    repository = MagicMock()
    repository.fetch_pending_skill_names.return_value = names
    return repository


@patch("aiEnrichSkill.llm_client.get_pipeline")
@patch("aiEnrichSkill.services.hf_enrichment._process_skill_batch")
def test_enrich_huggingface_batches_all_skills(mock_process_batch, mock_pipeline):
    repository = _make_repository(["Python", "Docker"])
    mock_pipeline.return_value = MagicMock()
    mock_process_batch.return_value = 2
    assert _enrich_huggingface(repository) == 2


def test_enrich_huggingface_no_skills():
    repository = _make_repository([])
    with capture_logs() as records:
        result = _enrich_huggingface(repository)
    assert result == 0
    skipped = [r for r in records if r["event"] == "jobs.skipped"]
    assert len(skipped) == 1
    assert skipped[0]["message"] == "No skills pending."
    assert skipped[0]["reason"] == "no_pending_skills"
    assert skipped[0]["limit"]


@patch("aiEnrichSkill.services.hf_enrichment.collector")
@patch("aiEnrichSkill.llm_client.get_pipeline")
@patch("aiEnrichSkill.services.hf_enrichment._process_skill_batch")
def test_enrich_huggingface_sets_pending(mock_process_batch, mock_pipeline, mock_collector):
    repository = _make_repository(["Python", "Docker"])
    mock_pipeline.return_value = MagicMock()
    mock_process_batch.return_value = 2
    _enrich_huggingface(repository)
    mock_collector.set_pending.assert_called_once_with("aiEnrichSkill", 2)


@patch("aiEnrichSkill.services.hf_enrichment.validate_learning_paths", return_value=[])
@patch("aiEnrichSkill.services.hf_enrichment.collector")
@patch("aiEnrichSkill.llm_utils.process_batch")
def test_process_skill_batch_on_success_records_metric_failure(mock_process_batch, mock_collector, _mock_validate):
    captured = run_process_skill_batch(mock_process_batch)
    captured["on_success"]({"name": "Python"}, "")
    assert_failure_metric(mock_collector, check_duration=True)


@patch("aiEnrichSkill.services.hf_enrichment.validate_learning_paths", return_value=[])
@patch("aiEnrichSkill.services.hf_enrichment.collector")
@patch("aiEnrichSkill.llm_utils.process_batch")
def test_process_skill_batch_on_success_with_valid_result(mock_process_batch, mock_collector, _mock_validate):
    captured = run_process_skill_batch(mock_process_batch)
    captured["on_success"]({"name": "Python"}, "**Summary**: Language. **Category**: Programming")
    assert mock_collector.record_job.call_args[0][2] is True


@patch("aiEnrichSkill.services.hf_enrichment.validate_learning_paths", return_value=["https://docs.python.org/"])
@patch("aiEnrichSkill.services.hf_enrichment.collector")
@patch("aiEnrichSkill.llm_utils.process_batch")
def test_process_skill_batch_persists_validated_learning_path(mock_process_batch, _mock_collector, _mock_validate):
    captured = run_process_skill_batch(mock_process_batch)
    output = "**Summary**: Language.\n**Category**: Programming\n**Learning Path**:\n- https://docs.python.org/"
    captured["on_success"]({"name": "Python"}, output)
    args = captured["repository"].save_skill_result.call_args[0]
    assert args[0] == "Python"
    assert args[3] == ["https://docs.python.org/"]


@patch("aiEnrichSkill.services.hf_enrichment.collector")
@patch("aiEnrichSkill.llm_utils.process_batch")
def test_process_skill_batch_on_error_records_metric(mock_process_batch, mock_collector):
    captured = run_process_skill_batch(mock_process_batch)
    captured["on_error"]({"name": "Python"}, Exception("timeout"))
    assert_failure_metric(mock_collector, check_duration=True)
    mock_collector.record_error.assert_called_once_with("aiEnrichSkill", "timeout")
