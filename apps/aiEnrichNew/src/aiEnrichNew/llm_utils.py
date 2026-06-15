import time
import torch
import traceback
from typing import List, Callable, Dict, Any, TypeVar

from commonlib.observability import get_logger
from .config import should_cleanup_gpu

T = TypeVar('T')

logger = get_logger("aiEnrichNew.llm_utils")


def process_batch(
    pipeline: Any,
    items: List[T],
    tokenizer_fn: Callable[[Any, List[dict]], str],
    build_messages_fn: Callable[[T], List[dict]],
    handle_result_fn: Callable[[T, str], None],
    handle_error_fn: Callable[[T, Exception], None],
    timeout_per_item: float,
    batch_description: str = "items"
) -> int:
    prompts = []
    valid_indices = []

    for i, item in enumerate(items):
        try:
            messages = build_messages_fn(item)
            prompt = tokenizer_fn(pipeline.tokenizer, messages)
            if prompt:
                prompts.append(prompt)
                valid_indices.append(i)
        except Exception as e:
            handle_error_fn(item, e)

    if not prompts:
        return 0

    success_count = 0
    try:
        batch_start = time.time()
        logger.info("batch.inference_start", batch_size=len(prompts), type=batch_description)
        timeout = timeout_per_item * len(prompts)
        outputs = pipeline(prompts, batch_size=len(prompts), max_time=timeout)
        batch_duration = time.time() - batch_start
        logger.info("batch.inference_complete", batch_size=len(prompts), type=batch_description, duration=batch_duration)

        for i, output in enumerate(outputs):
            original_idx = valid_indices[i]
            item = items[original_idx]
            try:
                generated_text = output[0]['generated_text']
                handle_result_fn(item, generated_text)
                success_count += 1
            except Exception as e:
                handle_error_fn(item, e)

    except Exception as e:
        logger.error("batch.inference_failed", type=batch_description, error=str(e))
        traceback.print_exc()
        for i in valid_indices:
            handle_error_fn(items[i], Exception(f"Batch Inference Failed: {e}"))

    if should_cleanup_gpu() and torch.cuda.is_available():
        torch.cuda.empty_cache()

    return success_count
