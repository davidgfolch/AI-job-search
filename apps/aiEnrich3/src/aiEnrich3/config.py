import os

def get_input_max_len() -> int:
    return int(os.environ.get("ENRICH_INPUT_MAX_LEN", 10000))

def get_batch_size() -> int:
    # Set standard batch size for CPU processing. Default slightly lower than LLM batches
    # as these run natively loop-by-loop.
    return int(os.environ.get("ENRICH_MAX_CONCURRENCY", 4))
