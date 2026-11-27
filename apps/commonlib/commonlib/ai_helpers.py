import re  # noqa: F401 - kept: `re` is patched by importers of this shared module

from commonlib.stringUtil import removeExtraEmptyLines
from commonlib.dateUtil import getDatetimeNowStr, getSeconds, getTimeUnits
from commonlib.environmentUtil import getEnv
from commonlib.systemUtil import isDocker
from commonlib.terminalColor import green, stripAnsi
from commonlib.terminalUtil import consoleTimer
from commonlib.wake_timer import WakeableTimer
from commonlib.observability import get_logger
from commonlib.ai_result_validation import (  # noqa: F401 - re-exported: extraction_contract and existing importers treat this module as the entry point
    HYBRID_INFO_PROMPT_ECHO_PHRASES, MAX_HYBRID_INFO_LEN, VALID_MODALITIES, _expand_parenthesized_skills,
    _normalizeModality, flatten_skill_groups, is_hybrid_info_prompt_echo, listsToString, validateResult,
)

logger = get_logger("commonlib.ai_helpers")

MAX_AI_ENRICH_ERROR_LEN = 500
RETRY_ERROR_PREFIX = "RETRY ERROR: "
MAX_AI_INPUT_CHARS = 30000
TOO_LONG_CONTEXT_REASON = "too long context"


def get_max_ai_input_chars() -> int:
    """Read per call so a .env edit applies without a restart."""
    return int(getEnv("AI_ENRICH_INPUT_MAX_LEN", str(MAX_AI_INPUT_CHARS)))


def is_context_too_long(text: str) -> bool:
    """Oversized inputs cannot finish within the job timeout, so they are skipped before dispatch."""
    return len(text or "") > get_max_ai_input_chars()


def printJob(processName, total, idx, id, title, company, inputLen):
    print(green(f'AI {processName} job {idx+1}/{max(total, idx + 1)} - {getDatetimeNowStr()} -> id={id}, title={title}, company={company} -> input length={inputLen}'))


def mapJob(job):
    title = job[1]
    company = job[3]
    markdown = removeExtraEmptyLines(job[2].decode("utf-8") if isinstance(job[2], bytes) else job[2])+'\n'  # DB markdown blob decoding if bytes
    return title, company, markdown


from commonlib.json_helpers import (  # noqa: E402 - kept below the job helpers so the import order of this shared module stays unchanged
    rawToJson
)


def footer(total, idx, totalCount, jobErrors:set, elapsed_time: float = None, job_elapsed: float = None, config: str = None):
    """Log the running progress of a batch: the `n/m` line is the human half of the record, the fields the queryable half.
    `elapsed_time` is the batch wall time behind the per-job media; `job_elapsed`, when given, is the current job's
    inference total, printed by `Time elapsed:`; `config` is the filter configuration the current job came from.
    `total` starts as the run's expected size and tracks the chunked drain, never dropping below the jobs processed."""
    total = max(total, idx + 1)
    fields = dict(processed=idx + 1, total=total, total_processed=totalCount, job_errors=len(jobErrors), **({'config': config} if config else {}))
    console = green(f"Processed jobs this run: {idx + 1}/{total}, total processed jobs: {totalCount}  Total job errors: {len(jobErrors)}" + (f"  Config: {config}" if config else ""))
    if job_elapsed is not None:
        fields['job_elapsed'] = getTimeUnits(job_elapsed)
    if elapsed_time is not None and (idx + 1) > 0:
        media = elapsed_time / (idx + 1)
        fields['elapsed'] = getTimeUnits(elapsed_time)
        fields['elapsed_per_job'] = getTimeUnits(media)
        shown = fields['job_elapsed'] if job_elapsed is not None else fields['elapsed']
        console += f", Time elapsed: {shown} (Media: {fields['elapsed_per_job']}/job)"
    elif job_elapsed is not None:
        console += f", Time elapsed: {fields['job_elapsed']}"
    logger.info("ai.batch_completed", console=console, **fields)


def logIdleWait(console_text: str, timeUnit: str, event: str, **fields):
    """Log that there was nothing to process, then wait before polling again.

    An idle loop is not a timer, so it does not emit `timer.started`: the caller names the
    event (`jobs.skipped`, `ai.retry_wait`) and `wait_seconds`
    travels on that one record instead of on a separate timer line.

    In a container the cycle is one rendered record: the human sentence travels as
    `message=`, so `docker-compose logs` shows the `*_skipped` event with its reason and
    wait as fields instead of a bare sentence. On a terminal `consoleTimer` keeps its
    countdown, which is the progress a person watching locally wants.
    """
    if not isDocker():
        consoleTimer(console_text, timeUnit)
        return
    seconds = getSeconds(timeUnit)
    logger.info(event, message=stripAnsi(console_text), wait_seconds=seconds, **fields)
    WakeableTimer().wait(seconds)


def idleWait(console_text: str, timeUnit: str):
    """Wait for the next poll without logging: this cycle's record was already logged.

    `aiEnrichSkill` uses it when the enrichment service has already emitted
    `jobs.skipped`, so a cycle stays one line in the container.
    """
    if not isDocker():
        consoleTimer(console_text, timeUnit)
        return
    WakeableTimer().wait(getSeconds(timeUnit))


def combineTaskResults(crewOutput, debug) -> dict:
    """Combina los resultados de todas las tareas en un único JSON"""
    result = {}
    # Use getattr or direct access assuming object structure
    raw = getattr(crewOutput, 'raw', None)
    if raw is None: # Fallback if passed dict or something else, though unlikely based on usage
         raw = str(crewOutput)
    mainResult = rawToJson(raw)
    if mainResult:
        if debug:
            logger.debug("ai.main_result", result=mainResult)
        result.update(mainResult)
    # Process individual task results if available
    tasks_output = getattr(crewOutput, 'tasks_output', None)
    if tasks_output:
        for task_idx, task_output in enumerate(tasks_output):
            task_raw = getattr(task_output, 'raw', str(task_output))
            taskResult = rawToJson(task_raw)
            if taskResult:
                if debug:
                    logger.debug("ai.task_result", task_index=task_idx, result=taskResult)
                for key, value in taskResult.items():
                    allowed = ["required_technologies", "optional_technologies", "salary", "modality", "experience_level", "responsibilities", "cv_match_percentage"]
                    if key in allowed and (key not in result or result[key] is None) and value is not None:
                        result[key] = value
    return result
