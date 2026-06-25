import time
import json
import traceback
from typing import List, Dict, Any, Tuple, Optional, Set

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.ai_helpers import footer, printJob, RETRY_ERROR_PREFIX
from commonlib.terminalColor import yellow, magenta, cyan, red
from commonlib.stopWatch import StopWatch
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

from ..pipeline import ExtractionPipeline
from ..config import get_input_max_len

logger = get_logger("aiEnrich3.job_enrichment")
collector = MetricsCollector()


def _save_job_result(repo: AiEnrichRepository, job_id: int, company: str, result: Dict[str, Any]):
    req_tech_str = ", ".join(result.get('required_skills', []))
    opt_tech_str = ", ".join(result.get('optional_skills', []))
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
        logger.error("job.error_update_failed", job_id=job_id)
    else:
        logger.warning("job.error_set", job_id=job_id)


def enrich_jobs(repo: AiEnrichRepository, pipeline: ExtractionPipeline, batch_size: int) -> int:
    total = repo.count_pending_enrichment()
    if total == 0:
        return 0

    logger.info("jobs.found", total=total, batch_size=batch_size, module="aiEnrich3")
    job_ids = repo.get_pending_enrichment_ids()
    logger.debug("job.pending_ids", ids=job_ids)

    jobs_buffer = _fetch_and_sort_jobs(repo, job_ids, sort_by_length=False)

    total_count = 0
    job_errors: Set[Tuple[int, str]] = set()
    overall_start_time = time.time()

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

    logger.info("job.retry", job_id=error_id)

    job_data_tuple = repo.get_job_to_retry(error_id)
    if job_data_tuple:
        job_data = {
            "id": job_data_tuple[0],
            "title": job_data_tuple[1],
            "markdown": job_data_tuple[2],
            "company": job_data_tuple[3]
        }
        dummy_errors: Set[Tuple[int, str]] = set()
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
                if "markdown" in job_data and job_data["markdown"]:
                    if isinstance(job_data['markdown'], bytes):
                        job_data['markdown'] = job_data['markdown'].decode('utf-8')
                    if len(job_data['markdown']) > max_len:
                        job_data['markdown'] = job_data['markdown'][:max_len]
                    job_data['length'] = len(job_data['markdown'])
                else:
                    job_data['length'] = 0
                jobs_buffer.append(job_data)
        except Exception as e:
            logger.error("job.fetch_failed", job_id=job_id, error=str(e))

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
    for idx, item in enumerate(batch_items):
        stop_watch = StopWatch()
        stop_watch.start()

        job_id = item['id']
        title = item.get('title', 'Unknown')
        company = item.get('company', 'Unknown')
        text = item.get('markdown', '')

        job_start = time.time()
        success = False
        try:
            result = pipeline.process_job(text)
            logger.info("job.result", job_id=job_id, result=result, duration=round(time.time() - job_start, 3))
            _save_job_result(repo, job_id, company, result)
            success = True

            elapsed = time.time() - start_time
            printJob(process_name, total, start_idx + idx, job_id, title, company, item.get('length', 0))
            footer(total, start_idx + idx, current_total_count + idx + 1, job_errors, elapsed)

        except Exception as ex:
            logger.error("job.failed", job_id=job_id, title=title, company=company, error=str(ex), traceback=traceback.format_exc())
            job_errors.add((job_id, f'{title} - {company}: {ex}'))
            prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
            error_msg = f"{prefix}{ex}"
            _update_error_state(repo, job_id, error_msg, process_name == "retry")

        duration = time.time() - job_start
        collector.record_job("aiEnrich3", duration, success)
        stop_watch.end()
