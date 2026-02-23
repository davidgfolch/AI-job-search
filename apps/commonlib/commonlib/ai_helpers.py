import json
import re

from commonlib.stringUtil import hasLen, removeExtraEmptyLines
from commonlib.dateUtil import getDatetimeNowStr, getTimeUnits
from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import updateFieldsQuery
from commonlib.terminalColor import green, red, yellow

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
            print(yellow(f'Removing no numbers salary: {salary}'))
            result.update({'salary': None})
        elif salary:
            regex = r'^(sueldo|salarios?|\(?según experiencia\)?)[: ]+(.+)'
            if hasLen(re.finditer(regex, salary, flags=re.I)):
                result.update({'salary': re.sub(regex, r'\2', salary, flags=re.I)})
    listsToString(result, ['required_technologies', 'optional_technologies'])
    _normalizeModality(result)
    # Validate cv_match_percentage
    cv_match = result.get('cv_match_percentage')
    if cv_match:
        try:
            match_value = int(cv_match)
            if match_value < 0 or match_value > 100:
                print(yellow(f'Invalid cv_match_percentage: {cv_match}, setting to None'))
                result.update({'cv_match_percentage': None})
        except (ValueError, TypeError):
            print(yellow(f'Invalid cv_match_percentage format: {cv_match}, setting to None'))
            result.update({'cv_match_percentage': None})


def _expand_parenthesized_skills(value: str) -> str:
    pattern = r"(\w[\w\s\-#+.]*)\s*\(([^)]+)\)"
    while re.search(pattern, value):
        value = re.sub(pattern, lambda m: f"{m.group(1).strip()}, {', '.join(x.strip() for x in m.group(2).split(','))}", value)
        value = re.sub(r", *,", ",", value)
    return value


def listsToString(result: dict[str, str], fields: list[str]):
    for f in fields:
        value = result.get(f, None)
        if not value:
            result[f] = None
        else:
            if isinstance(value, str):
                value = _expand_parenthesized_skills(value)
                items = [x.strip() for x in value.split(",")]
            elif isinstance(value, list):
                items = [str(x).strip() for x in value if x is not None]
            else:
                items = []
            unique_items = list(dict.fromkeys([x for x in items if x]))
            if unique_items:
                result[f] = ",".join(unique_items)
                if result[f].lower() in ['none specified', 'null']:
                    result[f]=None
            else:
                result[f] = None


def footer(total, idx, totalCount, jobErrors:set, elapsed_time: float = None):
    msg = f'Processed jobs this run: {idx+1}/{total}, total processed jobs: {totalCount}'
    if elapsed_time is not None and (idx + 1) > 0:
        media = elapsed_time / (idx + 1)
        msg += f', Time elapsed: {getTimeUnits(elapsed_time)} (Media: {getTimeUnits(media)}/job)'
    print(yellow(msg), red(f'  Total job errors: {len(jobErrors)}') if jobErrors else '', end='\n')


def combineTaskResults(crewOutput, debug) -> dict:
    """Combina los resultados de todas las tareas en un único JSON"""
    result = {}
    # Use getattr or direct access assuming object structure since we don't want crewai dependency here
    raw = getattr(crewOutput, 'raw', None)
    if raw is None: # Fallback if passed dict or something else, though unlikely based on usage
         raw = str(crewOutput)
    mainResult = rawToJson(raw)
    if mainResult:
        if debug:
            print(yellow(f'Main result: {json.dumps(mainResult, indent=2)}'))
        result.update(mainResult)
    # Process individual task results if available
    tasks_output = getattr(crewOutput, 'tasks_output', None)
    if tasks_output:
        for task_idx, task_output in enumerate(tasks_output):
            task_raw = getattr(task_output, 'raw', str(task_output))
            taskResult = rawToJson(task_raw)
            if taskResult:
                if debug:
                    print(yellow(f'Task {task_idx} result: {json.dumps(taskResult, indent=2)}'))
                for key, value in taskResult.items():
                    allowed = ["required_technologies", "optional_technologies", "salary", "modality", "experience_level", "responsibilities", "cv_match_percentage"]
                    if key in allowed and (key not in result or result[key] is None) and value is not None:
                        result[key] = value
    return result
