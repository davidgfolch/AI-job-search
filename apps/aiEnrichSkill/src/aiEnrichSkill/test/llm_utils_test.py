from unittest.mock import MagicMock, patch

from ..llm_utils import process_batch


def test_process_batch_success():
    pipeline = MagicMock()
    pipeline.tokenizer = MagicMock()
    items = [{"id": 1, "text": "item1"}, {"id": 2, "text": "item2"}]
    tokenizer_fn = MagicMock(side_effect=lambda t, m: f"prompt_{m[0]['content']}")
    build_messages_fn = MagicMock(side_effect=lambda item: [{"role": "user", "content": item["text"]}])
    handle_result_fn = MagicMock()
    handle_error_fn = MagicMock()

    pipeline.return_value = [
        [{"generated_text": "result1"}],
        [{"generated_text": "result2"}]
    ]

    count = process_batch(pipeline, items, tokenizer_fn, build_messages_fn, handle_result_fn, handle_error_fn, 10.0)
    assert count == 2
    handle_result_fn.assert_any_call(items[0], "result1")
    handle_result_fn.assert_any_call(items[1], "result2")
    handle_error_fn.assert_not_called()


def test_process_batch_empty():
    pipeline = MagicMock()
    tokenizer_fn = MagicMock()
    build_messages_fn = MagicMock()
    handle_result_fn = MagicMock()
    handle_error_fn = MagicMock()

    count = process_batch(pipeline, [], tokenizer_fn, build_messages_fn, handle_result_fn, handle_error_fn, 10.0)
    assert count == 0
    pipeline.assert_not_called()


def test_process_batch_tokenizer_error():
    pipeline = MagicMock()
    pipeline.tokenizer = MagicMock()
    items = [{"id": 1, "text": "item1"}, {"id": 2, "text": "item2"}]
    tokenizer_fn = MagicMock(side_effect=["prompt_item1", Exception("Tokenization error")])
    build_messages_fn = MagicMock(side_effect=lambda item: [{"role": "user", "content": item["text"]}])
    handle_result_fn = MagicMock()
    handle_error_fn = MagicMock()

    pipeline.return_value = [[{"generated_text": "result1"}]]

    count = process_batch(pipeline, items, tokenizer_fn, build_messages_fn, handle_result_fn, handle_error_fn, 10.0)
    assert count == 1
    handle_result_fn.assert_called_once_with(items[0], "result1")
    handle_error_fn.assert_called_once()


def test_process_batch_inference_error():
    pipeline = MagicMock()
    pipeline.tokenizer = MagicMock()
    items = [{"id": 1, "text": "item1"}, {"id": 2, "text": "item2"}]
    tokenizer_fn = MagicMock(side_effect=lambda t, m: f"prompt_{m[0]['content']}")
    build_messages_fn = MagicMock(side_effect=lambda item: [{"role": "user", "content": item["text"]}])
    handle_result_fn = MagicMock()
    handle_error_fn = MagicMock()

    pipeline.side_effect = Exception("Inference failed")

    count = process_batch(pipeline, items, tokenizer_fn, build_messages_fn, handle_result_fn, handle_error_fn, 10.0)
    assert count == 0
    assert handle_error_fn.call_count == 2
    handle_result_fn.assert_not_called()


@patch("aiEnrichSkill.llm_utils.get_gpu_cleanup")
@patch("torch.cuda.empty_cache")
@patch("torch.cuda.is_available")
def test_cleanup_gpu(mock_is_available, mock_empty_cache, mock_should_cleanup):
    mock_should_cleanup.return_value = True
    mock_is_available.return_value = True

    pipeline = MagicMock()
    pipeline.tokenizer = MagicMock()
    items = [{"id": 1, "text": "item1"}]
    tokenizer_fn = MagicMock(side_effect=lambda t, m: "prompt")
    build_messages_fn = MagicMock(side_effect=lambda item: [{"role": "user", "content": item["text"]}])
    handle_result_fn = MagicMock()
    handle_error_fn = MagicMock()
    pipeline.return_value = [[{"generated_text": "result1"}]]

    process_batch(pipeline, items, tokenizer_fn, build_messages_fn, handle_result_fn, handle_error_fn, 10.0)
    mock_empty_cache.assert_called_once()
