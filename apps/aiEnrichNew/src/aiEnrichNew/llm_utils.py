from typing import List, Callable, Dict, Any, TypeVar, Tuple
import time
import torch
import traceback
from commonlib.terminalColor import cyan, red, yellow
from .config import should_cleanup_gpu

T = TypeVar('T')
R = TypeVar('R')

def process_batch(
    pipeline: Any,
    items: List[T],
    tokenizer_fn: Callable[[Any, List[dict]], str], # (tokenizer, messages) -> prompt_str
    build_messages_fn: Callable[[T], List[dict]],
    handle_result_fn: Callable[[T, str], None],
    handle_error_fn: Callable[[T, Exception], None],
    timeout_per_item: float,
    batch_description: str = "items"
) -> int:
    """
    Generic batch processor for LLM inference.
    Executes the following pipeline:
    item -> build_messages -> tokenizer -> batch_inference -> handle_result
    
    This function handles:
    - Batching
    - Tokenization
    - Inference execution
    - Error boundaries
    - Resource cleanup
    """
    prompts = []
    valid_indices = []
    
    # 1. Prepare Prompts (Pure transformation + Tokenizer IO)
    for i, item in enumerate(items):
        try:
            messages = build_messages_fn(item)
            # Tokenizer is an IO/External dependency so we pass it in bound
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
        print(cyan(f"Running inference on batch of {len(prompts)} {batch_description}..."))
        timeout = timeout_per_item * len(prompts)
        
        # 2. Batch Inference (IO)
        outputs = pipeline(prompts, batch_size=len(prompts), max_time=timeout)
        
        # 3. Process Results (Callback for side effects or further purity)
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
        print(red(f"Critical error during batch inference for {batch_description}: {e}"))
        traceback.print_exc()
        # Fail all items in this batch that made it to inference
        for i in valid_indices:
            handle_error_fn(items[i], Exception(f"Batch Inference Failed: {e}"))
    
    # Cleanup memory
    if should_cleanup_gpu() and torch.cuda.is_available():
        torch.cuda.empty_cache()
            
    return success_count
