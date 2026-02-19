import unittest
from unittest.mock import MagicMock, patch
from ..llm_utils import process_batch

class TestLLMUtils(unittest.TestCase):

    def setUp(self):
        self.pipeline = MagicMock()
        self.pipeline.tokenizer = MagicMock()
        self.items = [{"id": 1, "text": "item1"}, {"id": 2, "text": "item2"}]
        self.tokenizer_fn = MagicMock(side_effect=lambda t, m: f"prompt_{m[0]['content']}")
        self.build_messages_fn = MagicMock(side_effect=lambda item: [{"role": "user", "content": item["text"]}])
        self.handle_result_fn = MagicMock()
        self.handle_error_fn = MagicMock()
        self.timeout = 10.0

    def test_process_batch_success(self):
        # Mock pipeline output
        self.pipeline.return_value = [
            [{"generated_text": "result1"}],
            [{"generated_text": "result2"}]
        ]

        count = process_batch(
            self.pipeline,
            self.items,
            self.tokenizer_fn,
            self.build_messages_fn,
            self.handle_result_fn,
            self.handle_error_fn,
            self.timeout
        )

        self.assertEqual(count, 2)
        self.handle_result_fn.assert_any_call(self.items[0], "result1")
        self.handle_result_fn.assert_any_call(self.items[1], "result2")
        self.handle_error_fn.assert_not_called()

    def test_process_batch_empty(self):
        count = process_batch(
            self.pipeline,
            [],
            self.tokenizer_fn,
            self.build_messages_fn,
            self.handle_result_fn,
            self.handle_error_fn,
            self.timeout
        )
        self.assertEqual(count, 0)
        self.pipeline.assert_not_called()

    def test_process_batch_tokenizer_error(self):
        # Fail tokenization for second item
        self.tokenizer_fn.side_effect = ["prompt_item1", Exception("Tokenization error")]

        # Pipeline should only receive one prompt
        self.pipeline.return_value = [[{"generated_text": "result1"}]]

        count = process_batch(
            self.pipeline,
            self.items,
            self.tokenizer_fn,
            self.build_messages_fn,
            self.handle_result_fn,
            self.handle_error_fn,
            self.timeout
        )

        self.assertEqual(count, 1)
        self.handle_result_fn.assert_called_once_with(self.items[0], "result1")
        self.handle_error_fn.assert_called_once() # Should be called for item 2
        args, _ = self.handle_error_fn.call_args
        self.assertEqual(args[0], self.items[1]) # item 2 failed
        self.assertIsInstance(args[1], Exception)

    def test_process_batch_inference_error(self):
        self.pipeline.side_effect = Exception("Inference failed")

        count = process_batch(
            self.pipeline,
            self.items,
            self.tokenizer_fn,
            self.build_messages_fn,
            self.handle_result_fn,
            self.handle_error_fn,
            self.timeout
        )

        self.assertEqual(count, 0)
        self.assertEqual(self.handle_error_fn.call_count, 2) # Both items failed
        self.handle_result_fn.assert_not_called()

    def test_process_batch_result_handling_error(self):
        self.pipeline.return_value = [
             [{"generated_text": "result1"}],
             [{"generated_text": "result2"}]
        ]
        # Fail result handling for first item
        self.handle_result_fn.side_effect = [Exception("Save error"), None]

        count = process_batch(
            self.pipeline,
            self.items,
            self.tokenizer_fn,
            self.build_messages_fn,
            self.handle_result_fn,
            self.handle_error_fn,
            self.timeout
        )

        self.assertEqual(count, 1) # Only 2nd succeeded
        self.handle_error_fn.assert_called_once()
        args, _ = self.handle_error_fn.call_args
        self.assertEqual(args[0], self.items[0])

    @patch("aiEnrichNew.llm_utils.should_cleanup_gpu")
    @patch("torch.cuda.empty_cache")
    @patch("torch.cuda.is_available")
    def test_cleanup_gpu(self, mock_is_available, mock_empty_cache, mock_should_cleanup):
        mock_should_cleanup.return_value = True
        mock_is_available.return_value = True
        
        self.pipeline.return_value = [
            [{"generated_text": "result1"}],
            [{"generated_text": "result2"}]
        ]

        process_batch(
            self.pipeline,
            self.items,
            self.tokenizer_fn,
            self.build_messages_fn,
            self.handle_result_fn,
            self.handle_error_fn,
            self.timeout
        )

        mock_empty_cache.assert_called_once()
