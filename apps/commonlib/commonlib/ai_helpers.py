import json
import re
import traceback

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


def rawToJson(raw: str) -> dict[str, str]:
    res = raw
    try:
        IM = re.I | re.M
        # remove Agent Thought or Note (from crewHelper)
        res = re.sub(r'\n(Thought|Note):(.*\n)*', '', res, flags=IM)
        # remove json prefix
        res = re.sub(r'(```(json)?\n?)', '', res, flags=IM) # Merged from jsonHelper/crewHelper
        res = re.sub(r'json *object *', '', res, flags=IM)
        # CrewHelper fixers
        res = fixJsonStartCurlyBraces(res)
        res = fixJsonEndCurlyBraces(res)
        res = fixJsonInvalidAttribute(res)
        # repl \& or \. (...) by & or .
        res = re.sub(r'\\([&.*-+#])', r'\1', res, re.I | re.M)
        return dict(json.loads(f'{res}', cls=LazyDecoder))
    except Exception as ex:
        printJsonException(ex, res, raw)
        raise ex


class LazyDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        regex_replacements = [
            (re.compile(r'([^\\])\\([^\\])'), r'\1\\\\\2'),
            (re.compile(r',(\s*])'), r'\1'),
        ]
        for regex, replacement in regex_replacements:
            s = regex.sub(replacement, s)
        return super().decode(s, **kwargs)


def printJsonException(ex: Exception, res: str, raw: str) -> None:
    print(red(f'Could not parse json after clean it: '))
    # Traceback is already printed by caller usually, but logic in crewHelper prints it.
    # jsonHelper commented it out. We will keep it but maybe concise?
    print(red(traceback.format_exc()))
    print(red(f'Json after clean:\n{res}'))
    print(yellow(f'Original json:\n{raw}'))
    raise ex


def fixJsonInvalidAttribute(raw):
    """Fixes LLM invalid json value, f.ex.:
    "salary": "xx" + "yy",
    "salary": "xx",",
    """
    raw = re.sub(r'" \+ "', ' + ', raw)
    # {"salary":
    # "$\text{Salary determined by the market and your experience} \\\$",
    raw = re.sub(r'"[$]\\text\{([^\}]+)\} \\\\\\\$"', r'\1', raw)
    return re.sub(r'(.+)",",', r'\1",', raw)


def fixJsonEndCurlyBraces(raw):
    raw = re.sub('"[)\\\\]', '"}', raw)
    raw = re.sub('[}]{2,}', '}', raw) # remove dobule curly braces at the end }}
    raw = re.sub(',[ \n]*[}]', '\n}', raw) # remove exta comma at the end ,}
    idx = raw.rfind('}')
    if idx > 0 and idx + 1 < len(raw):  # remove extra text after }
        return raw[0:idx+1]
    if idx == -1:  # sometimes LLM forgets to close }
        return raw + '}'
    return raw


def fixJsonStartCurlyBraces(raw):
    idx = raw.rfind('{')
    if idx > 0 and idx + 1 < len(raw):
        # remove extra text before {
        return raw[idx:]
    return raw


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
                    if key not in result and key in ["required_technologies", "optional_technologies", "salary", "experience_level", "responsibilities", "cv_match_percentage"]:
                        result[key] = value
    return result
