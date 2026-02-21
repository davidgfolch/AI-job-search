import time
import json
import traceback
from typing import List, Dict, Any, Tuple, Optional, Set

from commonlib.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.ai_helpers import footer, printJob, RETRY_ERROR_PREFIX
from commonlib.terminalColor import yellow, magenta, cyan, red, printHR
from commonlib.stopWatch import StopWatch

from ..pipeline import ExtractionPipeline
from ..config import get_input_max_len

def _save_job_result(repo: AiEnrichRepository, job_id: int, company: str, result: Dict[str, Any]):
    # Join the lists of skills into comma-separated strings for our DB schema
    req_tech_str = ", ".join(result.get('required_skills', []))
    opt_tech_str = ", ".join(result.get('optional_skills', []))
    
    # Empty strings should be NULL in DB
    req_tech_str = req_tech_str if req_tech_str else None
    opt_tech_str = opt_tech_str if opt_tech_str else None
    
    modality_val = result.get('modality', None)
    
    repo.update_enrichment(
        id=job_id, 
        salary=result.get('salary', None), 
        required_tech=req_tech_str,
        optional_tech=opt_tech_str,
        modality=modality_val
    )

def _update_error_state(repo: AiEnrichRepository, job_id: int, error_msg: str, is_retry: bool):
    if repo.update_enrichment_error(job_id, error_msg, True) == 0:
        print(red(f"could not update ai_enrich_error, id={job_id}"))
    else:
        print(yellow(f"ai_enrich_error set, id={job_id}"))

# --- Pipeline Construction ---

def enrich_jobs(repo: AiEnrichRepository, pipeline: ExtractionPipeline, batch_size: int) -> int:
    total = repo.count_pending_enrichment()
    if total == 0:
        return 0

    print()
    print(f'{total} jobs to be ai_enriched using local CPU Extractors (Processing in batches of {batch_size})...')
    
    # 1. Fetch & Sort (Optimization Step)
    job_ids = repo.get_pending_enrichment_ids()
    print(yellow(f'Pending Job IDs: {job_ids}'))
    
    jobs_buffer = _fetch_and_sort_jobs(repo, job_ids, sort_by_length=False)
    
    total_count = 0
    job_errors: Set[Tuple[int, str]] = set()
    overall_start_time = time.time()
    
    # 2. Local Batch Processing
    for i in range(0, len(jobs_buffer), batch_size):
        batch_items = jobs_buffer[i:i + batch_size]
        _process_job_batch_local(
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

def retry_failed_job(repo: AiEnrichRepository, pipeline: ExtractionPipeline) -> int:
    error_id = repo.get_enrichment_error_id_retry()
    if error_id is None:
        return 0
        
    printHR(yellow)
    print(yellow(f"Retrying failed job id={error_id}..."))
    
    job_data_tuple = repo.get_job_to_retry(error_id)
    if job_data_tuple:
        job_data = {
            "id": job_data_tuple[0],
            "title": job_data_tuple[1],
            "markdown": job_data_tuple[2],
            "company": job_data_tuple[3]
        }
        # We process this single job through the local pipeline
        dummy_errors: Set[Tuple[int, str]] = set()
        # Ensure job formatting matches expected
        if "markdown" in job_data and job_data["markdown"]:
            if isinstance(job_data['markdown'], bytes):
                job_data['markdown'] = job_data['markdown'].decode('utf-8')
            job_data['length'] = len(job_data['markdown'])
        else:
            job_data['length'] = 0
            
        _process_job_batch_local(
            repo, 
            pipeline, 
            [job_data], 
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
    max_len = get_input_max_len()
    
    for job_id in job_ids:
        try:
            job_data_tuple = repo.get_job_to_enrich(job_id)
            if job_data_tuple:
                job_data = {
                    "id": job_data_tuple[0],
                    "title": job_data_tuple[1],
                    "markdown": job_data_tuple[2],
                    "company": job_data_tuple[3]
                }
                # We do basic formatting here instead of domain mapper since it's simple
                if "markdown" in job_data and job_data["markdown"]:
                    if isinstance(job_data['markdown'], bytes):
                        job_data['markdown'] = job_data['markdown'].decode('utf-8')
                        
                    # Truncate to save CPU processing time if the job is excessively long
                    if len(job_data['markdown']) > max_len:
                        job_data['markdown'] = job_data['markdown'][:max_len]
                        
                    job_data['length'] = len(job_data['markdown'])
                else:
                    job_data['length'] = 0
                jobs_buffer.append(job_data)
        except Exception as e:
            print(red(f"Error fetching job {job_id} for sorting: {e}"))
    
    # Sort by character length. Crucial optimization for local models if batching, 
    # as it minimizes padding tokens (although GLiNER/mDeBERTa pipeline loops internally).
    if sort_by_length:
        jobs_buffer.sort(key=lambda x: x['length'])
    return jobs_buffer

def _process_job_batch_local(
    repo: AiEnrichRepository, 
    pipeline: ExtractionPipeline, 
    batch_items: List[Dict[str, Any]], 
    total: int, 
    start_idx: int, 
    process_name: str, 
    start_time: float,
    current_total_count: int,
    job_errors: Set[Tuple[int, str]]
):
    printHR(yellow)

    for idx, item in enumerate(batch_items):
        stop_watch = StopWatch()
        stop_watch.start()
        
        job_id = item['id']
        title = item.get('title', 'Unknown')
        company = item.get('company', 'Unknown')
        text = item.get('markdown', '')
        
        try:
            # Core business logic: Run ML extraction sequentially locally
            result = pipeline.process_job(text)
            
            print(f'[{job_id}] Result:\n', magenta(json.dumps(result, indent=2)))
            
            # Save (Side Effect)
            _save_job_result(repo, job_id, company, result)
            
            # Logging (Side Effect)
            elapsed = time.time() - start_time
            printJob(process_name, total, start_idx + idx, job_id, title, company, item.get('length', 0))
            footer(total, start_idx + idx, current_total_count + idx + 1, job_errors, elapsed)
            
        except Exception as ex:
            print(red(traceback.format_exc()))
            job_errors.add((job_id, f'{title} - {company}: {ex}'))
            
            prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
            error_msg = f"{prefix}{ex}"
            
            _update_error_state(repo, job_id, error_msg, process_name == "retry")
            
        stop_watch.end()
