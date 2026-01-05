import json
import re
import traceback

from crewai.crews.crew_output import CrewOutput

from commonlib.util import hasLen, removeExtraEmptyLines
from commonlib.dateUtil import getDatetimeNowStr
from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import updateFieldsQuery
from commonlib.terminalColor import green, red, yellow

MAX_AI_ENRICH_ERROR_LEN = 500

def printJob(processName, total, idx, id, title, company, inputLen):
    print(green(f'AI {processName} job {idx+1}/{total} - {getDatetimeNowStr()} -> id={id}, title={title}, company={company} -> input length={inputLen}'))


def mapJob(job):
    title = job[1]
    company = job[3]
    markdown = removeExtraEmptyLines(job[2].decode("utf-8"))  # DB markdown blob decoding
    return title, company, markdown


def saveError(mysql: MysqlUtil, jobErrors: set, id, title, company, ex, dataExtractor:bool):
    print(red(traceback.format_exc()))
    jobErrors.add((id, f'{title} - {company}: {ex}'))
    aiEnrichError = str(ex)[:MAX_AI_ENRICH_ERROR_LEN]
    fields = {'ai_enrich_error': aiEnrichError, 'ai_enriched': True} if dataExtractor else {'cv_match_percentage': -1}
    query, params = updateFieldsQuery([id], fields)
    count = mysql.executeAndCommit(query, params)
    if count == 0:
        print(red(f"could not update ai_enrich_error, id={id}"))
    else:
        print(yellow(f"ai_enrich_error set, id={id}"))


def rawToJson(raw: str) -> dict[str, str]:
    res = raw
    try:
        IM = re.I | re.M
        # remove Agent Thought or Note
        res = re.sub(r'\n(Thought|Note):(.*\n)*', '', res, flags=IM)
        # remove json prefix
        res = re.sub(r'json *object *', '', res, flags=IM)
        res = re.sub(r'(```)', '', res, flags=IM)
        res = fixJsonStartCurlyBraces(res)
        res = fixJsonEndCurlyBraces(res)
        res = fixJsonInvalidAttribute(res)
        # repl \& or \. (...) by & or .
        res = re.sub(r'\\([&.*-+#])', r'\1', res, re.I | re.M)
        # res = fixInvalidUnicode(res)
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
    print(red(traceback.format_exc()))
    print(red(f'Json after clean:\n{res}'))
    print(yellow(f'Original json:\n{raw}'))
    raise ex


# def fixInvalidUnicode(res):
#     res = re.sub('\\\\u00ai', '\u00ad', res)  # Ã¡
#     res = re.sub('\\\\u00f3', '\u00ed', res)  # Ã­
#     res = re.sub('\\\\u00f3', '\u00ed', res)  # Ã­
#     return res


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
        if re.match(r'^[^0-9]+$', salary):  # doesn't contain numbers
            print(yellow(f'Removing no numbers salary: {salary}'))
            result.update({'salary': None})
        else:
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


def listsToString(result: dict[str, str], fields: list[str]):
    for f in fields:
        value = result.get(f, None)
        if not value:
            result[f] = None
        elif isinstance(value, list):
            result[f] = ','.join(value)



def combineTaskResults(crewOutput: CrewOutput, debug) -> dict:
    """Combina los resultados de todas las tareas en un único JSON"""
    result = {}
    mainResult = rawToJson(crewOutput.raw)
    if mainResult:
        if debug:
            print(yellow(f'Main result: {json.dumps(mainResult, indent=2)}'))
        result.update(mainResult)
    if result is None:
        # Procesar los resultados de las tareas individuales
        if hasattr(crewOutput, 'tasks_output') and crewOutput.tasks_output:
            for task_idx, task_output in enumerate(crewOutput.tasks_output):
                taskResult = rawToJson(task_output.raw)
                if taskResult:
                    if debug:
                        print(yellow(f'Task {task_idx} result: {json.dumps(taskResult, indent=2)}'))
                    for key, value in taskResult.items():
                        if key not in result and key in ["required_technologies", "optional_technologies", "salary", "experience_level", "responsibilities", "cv_match_percentage"]:
                            result[key] = value
    return result

def footer(total, idx, totalCount, jobErrors:set):
    print(yellow(f'Processed jobs this run: {idx+1}/{total}, total processed jobs: {totalCount}'),
          end='\n' if len(jobErrors)==0 else ' ')
    if jobErrors:
        print(red(f'Total job errors: {len(jobErrors)}'))
        # [print(yellow(f'{e[0]} - {e[1]}')) for e in jobErrors]


