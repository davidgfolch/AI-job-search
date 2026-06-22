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
