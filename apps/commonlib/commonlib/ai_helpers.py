import re

from commonlib.stringUtil import hasLen, removeExtraEmptyLines
from commonlib.dateUtil import getDatetimeNowStr, getSeconds, getTimeUnits
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import updateFieldsQuery
from commonlib.systemUtil import isDocker
from commonlib.terminalColor import green, stripAnsi
from commonlib.terminalUtil import consoleTimer
from commonlib.wake_timer import WakeableTimer
from commonlib.observability import get_logger

logger = get_logger("commonlib.ai_helpers")

MAX_AI_ENRICH_ERROR_LEN = 500
RETRY_ERROR_PREFIX = "RETRY ERROR: "

def printJob(processName, total, idx, id, title, company, inputLen):
    print(green(f'AI {processName} job {idx+1}/{total} - {getDatetimeNowStr()} -> id={id}, title={title}, company={company} -> input length={inputLen}'))


def mapJob(job):
    title = job[1]
    company = job[3]
    markdown = removeExtraEmptyLines(job[2].decode("utf-8") if isinstance(job[2], bytes) else job[2])+'\n'  # DB markdown blob decoding if bytes
    return title, company, markdown


from commonlib.json_helpers import (
    rawToJson, decode_unicode_escapes, LazyDecoder, printJsonException,
    fixJsonInvalidAttribute, fixJsonEndCurlyBraces, fixJsonStartCurlyBraces
)


VALID_MODALITIES = {'REMOTE', 'HYBRID', 'ON_SITE'}

def _normalizeModality(result: dict) -> None:
    modality = result.get('modality')
    if not modality:
        result['modality'] = None
        return
    normalized = str(modality).upper().strip()
    result['modality'] = normalized if normalized in VALID_MODALITIES else None

def validateResult(result: dict[str, str]):
    salary = result.get('salary')
    if salary:  # infojobs
        if isinstance(salary, dict):
            if 'min' in salary and 'max' in salary:
                salary = f"{salary.get('min')}-{salary.get('max')}"
            elif 'amount' in salary:
                val = salary.get('amount')
                salary = str(val) if val is not None else None
            else:
                salary = str(salary)
            result['salary'] = salary
        elif salary is not None and not isinstance(salary, str):
            salary = str(salary)
        if salary and re.match(r'^[^0-9]+$', salary):  # doesn't contain numbers
            logger.warning("ai.invalid_salary", reason="no_numbers", salary=salary)
            result.update({'salary': None})
        elif salary:
            regex = r'^(sueldo|salarios?|\(?según experiencia\)?)[: ]+(.+)'
            if hasLen(re.finditer(regex, salary, flags=re.I)):
                result.update({'salary': re.sub(regex, r'\2', salary, flags=re.I)})
    listsToString(result, ['required_technologies', 'optional_technologies'])
    if not result.get('required_technologies') and not result.get('optional_technologies'):
        logger.warning("ai.no_technologies", reason="both_technology_fields_empty")
    _normalizeModality(result)
    # Validate cv_match_percentage
    cv_match = result.get('cv_match_percentage')
    if cv_match:
        try:
            match_value = int(cv_match)
            if match_value < 0 or match_value > 100:
                logger.warning("ai.invalid_cv_match", reason="out_of_range", cv_match_percentage=cv_match)
                result.update({'cv_match_percentage': None})
        except (ValueError, TypeError):
            logger.warning("ai.invalid_cv_match", reason="not_a_number", cv_match_percentage=cv_match)
            result.update({'cv_match_percentage': None})


def _expand_parenthesized_skills(value: str) -> str:
    pattern = r"(\w[\w\s\-#+.]*)\s*\(([^)]+)\)"
    while re.search(pattern, value):
        value = re.sub(pattern, lambda m: f"{m.group(1).strip()}, {', '.join(x.strip() for x in m.group(2).split(','))}", value)
        value = re.sub(r", *,", ",", value)
    return value


def flatten_skill_groups(value) -> list[str]:
    if isinstance(value, str):
        value = _expand_parenthesized_skills(value)
        items = [x.strip() for x in value.split(",")]
    elif isinstance(value, list):
        items = []
        for item in value:
            if item is None:
                continue
            expanded = _expand_parenthesized_skills(str(item).strip())
            items.extend(x.strip() for x in expanded.split(","))
    else:
        items = []
    return list(dict.fromkeys([x for x in items if x]))


def listsToString(result: dict[str, str], fields: list[str]):
    for f in fields:
        value = result.get(f, None)
        if not value:
            result[f] = None
        else:
            unique_items = flatten_skill_groups(value)
            if unique_items:
                result[f] = ",".join(unique_items)
                if result[f].lower() in ['none specified', 'null']:
                    result[f]=None
            else:
                result[f] = None


def footer(total, idx, totalCount, jobErrors:set, elapsed_time: float = None, job_elapsed: float = None, config: str = None):
    """Log the running progress of a batch: the `n/m` line is the human half of the record, the fields the queryable half.
    `elapsed_time` is the batch wall time behind the per-job media; `job_elapsed`, when given, is the current job's
    inference total and is what `Time elapsed:` prints, so a progress line reports how long the job just finished took.
    `config` is the filter configuration the current job came from, shown on the progress line.
    """
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
