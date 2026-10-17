from unittest.mock import MagicMock


def capture_process_batch_callbacks(mock_process_batch):
    captured = {}

    def side_effect(pipeline, batch_items, apply_template, build_messages, on_success, on_error, timeout, name):
        captured["on_success"] = on_success
        captured["on_error"] = on_error

    mock_process_batch.side_effect = side_effect
    return captured


def make_ollama_mocks(mock_build, mock_query, mock_parse=None, query_result: str | None = "**Summary**: Test. **Category**: Language", parse_result=("Test", "Language")):
    mock_build.return_value = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "user"}
    ]
    mock_query.return_value = query_result
    if mock_parse:
        mock_parse.return_value = parse_result


def run_enrich_ollama(mock_process, name="Python", context="context"):
    from ..enrichment_service import _enrich_ollama
    generator_called = []
    def side_effect(mysql, generate_fn, limit, check_empty_description_only):
        generator_called.append(generate_fn(name, context))
        return 1
    mock_process.side_effect = side_effect
    return _enrich_ollama(MagicMock()), generator_called


def assert_failure_metric(mock_collector, check_duration=False):
    mock_collector.record_job.assert_called_once()
    args = mock_collector.record_job.call_args[0]
    assert args[0] == "aiEnrichSkill"
    if check_duration:
        assert isinstance(args[1], float)
    assert args[2] is False


def run_process_skill_batch(mock_process_batch, with_error=False):
    from ..enrichment_service import _process_skill_batch

    captured = capture_process_batch_callbacks(mock_process_batch)
    mysql = MagicMock()
    pipeline = MagicMock()
    batch_items = [{"name": "Python"}]

    _process_skill_batch(mysql, pipeline, batch_items, 0, 1, 0, 1000.0)

    assert "on_success" in captured
    if with_error:
        captured["on_error"]({"name": "Python"}, Exception("timeout"))
    return captured
