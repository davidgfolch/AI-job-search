import json
import re
import traceback

from crewai.crews.crew_output import CrewOutput

from ai_job_search.tools.util import (getDatetimeNowStr, hasLen, removeExtraEmptyLines)
from ai_job_search.tools.mysqlUtil import (QRY_FIND_JOBS_IDS_FOR_ENRICHMENT, updateFieldsQuery)
from ai_job_search.tools.terminalColor import green, red, yellow

MAX_AI_ENRICH_ERROR_LEN = 500

def printJob(total, idx, id, title, company):
    print(green(f'Job {idx+1}/{total} Started at: {getDatetimeNowStr()} -> id={id}, title={title}, company={company}'))


def mapJob(job):
    title = job[1]
    company = job[3]
    markdown = removeExtraEmptyLines(job[2].decode("utf-8"))  # DB markdown blob decoding
    return title, company, markdown


def saveError(mysql, jobErrors, id, title, company, ex):
    print(red(traceback.format_exc()))
    jobErrors.add((id, f'{title} - {company}: {ex}'))
    aiEnrichError = str(ex)[:MAX_AI_ENRICH_ERROR_LEN]
    params = {'ai_enrich_error': aiEnrichError,
              'ai_enriched': True}
    query, params = updateFieldsQuery([id], params)
    count = mysql.executeAndCommit(query, params)
    if count == 0:
        print(yellow(f"ai_enrich_error set, id={id}"))
    else:
        print(red(f"could not update ai_enrich_error, id={id}"))


def getJobIdsList(mysql) -> list[int]:
    jobIds = [row[0] for row in mysql.fetchAll(QRY_FIND_JOBS_IDS_FOR_ENRICHMENT)]
    print(yellow(f'{jobIds}'))
    return jobIds


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
    print(red(traceback.format_exc()))
    print(red(f'Could not parse json after clean it: {ex}'))
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
    raw = re.sub('"[}]{2,}', '"}', raw) # remove dobule curly braces at the end }}
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
    try:  # Procesar el resultado principal (extractor task)
        mainResult = rawToJson(crewOutput.raw)
        if mainResult:
            if debug:
                print(yellow(f'Main result: {json.dumps(mainResult, indent=2)}'))
            result.update(mainResult)
    except Exception as e:
        print(red(f'Error parsing main result: {e}'))

    # Procesar los resultados de las tareas individuales
    if hasattr(crewOutput, 'tasks_output') and crewOutput.tasks_output:
        for task_idx, task_output in enumerate(crewOutput.tasks_output):
            try:
                # Intentar parsear el output de cada tarea
                taskResult = rawToJson(task_output.raw)
                if taskResult:
                    if debug:
                        print(yellow(f'Task {task_idx} result: {json.dumps(taskResult, indent=2)}'))
                    for key, value in taskResult.items():
                        if key not in result and key in ["required_technologies", "optional_technologies", "salary", "experience_level", "responsibilities", "cv_match_percentage"]:
                            result[key] = value
            except Exception as e:
                print(red(f'Error parsing task {task_idx} result: {e}'))
    return result
