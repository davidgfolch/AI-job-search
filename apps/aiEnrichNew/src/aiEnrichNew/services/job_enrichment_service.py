import time
import json
import traceback
from typing import List, Dict, Any, Tuple, Optional, Set

from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.aiEnrichRepository import AiEnrichRepository
from commonlib.ai_helpers import footer, printJob, RETRY_ERROR_PREFIX
from commonlib.terminalColor import yellow, magenta, cyan, red, printHR
from commonlib.stopWatch import StopWatch
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector

from ..config import get_input_max_len, get_enrich_timeout_job
from ..llm_utils import process_batch
from ..domain.mappers import map_db_job_to_domain, build_job_prompt_messages
from ..domain.parsers import parse_job_enrichment_result

logger = get_logger("aiEnrichNew.job_enrichment")
collector = MetricsCollector()


def _save_job_result(repo: AiEnrichRepository, id: int, company: str, result: Dict[str, Any]):
    repo.update_enrichment(
        id,
        result.get('salary', None),
        result.get('required_technologies', None),
        result.get('optional_technologies', None),
        result.get('modality', None)
    )


def _update_error_state(repo: AiEnrichRepository, id: int, error_msg: str, is_retry: bool):
    if repo.update_enrichment_error(id, error_msg, True) == 0:
        logger.error("job.error_update_failed", job_id=id)
    else:
        logger.warning("job.error_set", job_id=id)


def enrich_jobs(repo: AiEnrichRepository, pipeline: Any, batch_size: int) -> int:
    total = repo.count_pending_enrichment()
    if total == 0:
        return 0

    logger.info("jobs.found", total=total, batch_size=batch_size, module="aiEnrichNew")
    job_ids = repo.get_pending_enrichment_ids()
    logger.debug("job.pending_ids", ids=job_ids)

    jobs_buffer = _fetch_and_sort_jobs(repo, job_ids, sort_by_length=True)

    total_count = 0
    job_errors: Set[Tuple[int, str]] = set()
    overall_start_time = time.time()

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

    logger.info("job.retry", job_id=error_id)

    job_data = repo.get_job_to_retry(error_id)
    if job_data:
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
            logger.error("job.fetch_failed", job_id=id, error=str(e))

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
    stop_watch = StopWatch()
    stop_watch.start()

    def apply_template(tokenizer, messages):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    _timing = {"last": time.time()}

    def on_success(item: Dict[str, Any], generated_text: str):
        job_id = item['id']
        company = item['company']
        now = time.time()
        job_duration = now - _timing["last"]
        _timing["last"] = now

        result = parse_job_enrichment_result(generated_text)
        logger.info("job.result", job_id=job_id, result=result, duration=round(job_duration, 3))

        if result is not None:
            _save_job_result(repo, job_id, company, result)
            collector.record_job("aiEnrichNew", time.time() - start_time, True)

        elapsed = time.time() - start_time
        idx = batch_items.index(item)
        printJob(process_name, total, start_idx + idx, job_id, item['title'], company, item['length'])
        footer(total, start_idx + idx, current_total_count + idx + 1, job_errors, elapsed)

    def on_error(item: Dict[str, Any], ex: Exception):
        job_id = item['id']
        title = item['title']
        company = item['company']

        logger.error("job.failed", job_id=job_id, title=title, company=company, error=str(ex), traceback=traceback.format_exc())
        job_errors.add((job_id, f'{title} - {company}: {ex}'))

        prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
        error_msg = f"{prefix}{ex}"

        _update_error_state(repo, job_id, error_msg, process_name == "retry")

    process_batch(
        pipeline,
        batch_items,
        apply_template,
        build_job_prompt_messages,
        on_success,
        on_error,
        get_enrich_timeout_job(),
        "jobs"
    )

    stop_watch.end()
