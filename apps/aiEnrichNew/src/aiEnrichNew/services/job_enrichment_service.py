import time
import json
import traceback
from typing import List, Dict, Any, Tuple, Optional, Set

from commonlib.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.ai_helpers import footer, printJob, RETRY_ERROR_PREFIX
from commonlib.terminalColor import yellow, magenta, cyan, red, printHR
from commonlib.stopWatch import StopWatch

from ..config import get_input_max_len, get_enrich_timeout_job
from ..llm_utils import process_batch
from ..domain.mappers import map_db_job_to_domain, build_job_prompt_messages
from ..domain.parsers import parse_job_enrichment_result

# --- Infrastructure / Side Effects (Saving) ---

def _save_job_result(repo: AiEnrichRepository, id: int, company: str, result: Dict[str, Any]):
    repo.update_enrichment(
        id, 
        result.get('salary', None), 
        result.get('required_technologies', None),
        result.get('optional_technologies', None)
    )

def _update_error_state(repo: AiEnrichRepository, id: int, error_msg: str, is_retry: bool):
    if repo.update_enrichment_error(id, error_msg, True) == 0:
        print(red(f"could not update ai_enrich_error, id={id}"))
    else:
        print(yellow(f"ai_enrich_error set, id={id}"))

# --- Pipeline Construction ---

def enrich_jobs(repo: AiEnrichRepository, pipeline: Any, batch_size: int) -> int:
    total = repo.count_pending_enrichment()
    if total == 0:
        return 0

    print()
    print(f'{total} jobs to be ai_enriched (Processing in batches of {batch_size})...')
    
    # 1. Fetch & Sort (Optimization Step)
    job_ids = repo.get_pending_enrichment_ids()
    print(yellow(f'{job_ids}'))
    
    jobs_buffer = _fetch_and_sort_jobs(repo, job_ids, sort_by_length=True)
    
    total_count = 0
    job_errors: Set[Tuple[int, str]] = set()
    overall_start_time = time.time()
    
    # 2. Batch Processing
    for i in range(0, len(jobs_buffer), batch_size):
        batch_items = jobs_buffer[i:i + batch_size]
        _process_job_batch_pipeline(
            repo, 
            pipeline, 
            batch_items, 
            total, 
            i, 
            "enrich", 
            overall_start_time,
            total_count,
            job_errors
        )
        total_count += len(batch_items)

    return total

def retry_failed_job(repo: AiEnrichRepository, pipeline: Any) -> int:
    error_id = repo.get_enrichment_error_id_retry()
    if error_id is None:
        return 0
        
    printHR(yellow)
    print(yellow(f"Retrying failed job id={error_id}..."))
    
    job_data = repo.get_job_to_retry(error_id)
    if job_data:
        # Map to domain object
        job_domain = map_db_job_to_domain(job_data)
        
        dummy_errors: Set[Tuple[int, str]] = set()
        _process_job_batch_pipeline(
            repo, 
            pipeline, 
            [job_domain], 
            1, 
            0, 
            "retry", 
            time.time(),
            0,
            dummy_errors
        )
        return 1
    return 0

def _fetch_and_sort_jobs(repo: AiEnrichRepository, job_ids: List[int], sort_by_length: bool = True) -> List[Dict[str, Any]]:
    jobs_buffer = []
    for id in job_ids:
        try:
            job_data = repo.get_job_to_enrich(id)
            if job_data:
                jobs_buffer.append(map_db_job_to_domain(job_data))
        except Exception as e:
            print(red(f"Error fetching job {id} for sorting: {e}"))
    
    if sort_by_length:
        jobs_buffer.sort(key=lambda x: x['length'])
    return jobs_buffer

def _process_job_batch_pipeline(
    repo: AiEnrichRepository, 
    pipeline: Any, 
    batch_items: List[Dict[str, Any]], 
    total: int, 
    start_idx: int, 
    process_name: str, 
    start_time: float,
    current_total_count: int,
    job_errors: Set[Tuple[int, str]]
):
    printHR(yellow)
    stop_watch = StopWatch()
    stop_watch.start()

    # --- Handlers Closure ---
    
    # Adapter for tokenizer: binds tokenizer instance
    def apply_template(tokenizer, messages):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def on_success(item: Dict[str, Any], generated_text: str):
        job_id = item['id']
        company = item['company']
        
        # Parse (Pure)
        result = parse_job_enrichment_result(generated_text)
        print(f'[{job_id}] Result:\n', magenta(json.dumps(result, indent=2)))
        
        # Save (Side Effect)
        if result is not None:
            _save_job_result(repo, job_id, company, result)
            
        # Logging (Side Effect)
        elapsed = time.time() - start_time
        idx = batch_items.index(item)
        # Note: Printing logic for current item
        printJob(process_name, total, start_idx + idx, job_id, item['title'], company, item['length'])
        footer(total, start_idx + idx, current_total_count + idx + 1, job_errors, elapsed)

    def on_error(item: Dict[str, Any], ex: Exception):
        job_id = item['id']
        title = item['title']
        company = item['company']
        
        print(red(traceback.format_exc()))
        job_errors.add((job_id, f'{title} - {company}: {ex}'))
        
        prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
        error_msg = f"{prefix}{ex}"
        
        _update_error_state(repo, job_id, error_msg, process_name == "retry")

    # Execute Generic Batch Processor
    process_batch(
        pipeline,
        batch_items,
        apply_template,         # Tokenizer adapter
        build_job_prompt_messages, # Pure Message Builder
        on_success,             # Success Handler (Parse + Save)
        on_error,               # Error Handler
        get_enrich_timeout_job(),
        "jobs"
    )
    
    stop_watch.end()
