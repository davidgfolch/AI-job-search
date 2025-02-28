import datetime
import json
import re
import traceback
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.flow.flow import Flow, start
from crewai.crews.crew_output import CrewOutput
from langchain_google_genai import ChatGoogleGenerativeAI
import openai
from ai_job_search.tools.stopWatch import StopWatch
from ai_job_search.tools.terminalColor import printHR, red, yellow
from ai_job_search.tools.mysqlUtil import (
    QRY_COUNT_JOBS_FOR_ENRICHMENT, QRY_FIND_JOB_FOR_ENRICHMENT,
    QRY_FIND_JOBS_IDS_FOR_ENRICHMENT, MysqlUtil, updateFieldsQuery)
from ai_job_search.tools.util import (
    AI_ENRICHMENT_JOB_TIMEOUT_MINUTES, getEnv,
    hasLen, removeExtraEmptyLines, consoleTimer)

MAX_AI_ENRICH_ERROR_LEN = 500

OPENAI_API_KEY = getEnv('OPENAI_API_KEY')
GEMINI_API_KEY = getEnv('GEMINI_API_KEY')

if OPENAI_API_KEY:
    model = "o1-preview-2024-09-12"  # gpt-3.5-turbo,  gpt-4o-mini
    LLM_CFG = LLM(model=model,
                  base_url="https://api.openai.com/v1",
                  api_key=OPENAI_API_KEY,
                  temperature=0)
elif GEMINI_API_KEY:
    # TODO: README: gcloud auth application-default login
    LLM_CFG = ChatGoogleGenerativeAI(model='gemini-1.5-flash',
                                     verbose=True,
                                     temperature=0,
                                     goggle_api_key=GEMINI_API_KEY)
else:
    LLM_CFG = LLM(
        model="ollama/llama3.2",
        # model="ollama/nuextract",  # hangs on local ollama
        # model="ollama/deepseek-r1:8b",  # no GPU inference
        base_url="http://localhost:11434",
        temperature=0)
mysql = None


class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        global mysql
        while True:
            with MysqlUtil() as mysql:
                total = mysql.count(QRY_COUNT_JOBS_FOR_ENRICHMENT)
                if total == 0:
                    consoleTimer("All jobs are already AI enriched, ", '1m')
                    continue
                print(f'{total} jobs to be ai_enriched...')
                self.enrichJobs(total)
                print(yellow(''*60))
                print(yellow('ALL ROWS PROCESSES!'))
                print(yellow(''*60))

    def enrichJobs(self, total):
        jobErrors = set[tuple[int, str]]()
        crew: Crew = AiJobSearch().crew()
        stopWatch = StopWatch()
        for idx, id in enumerate(getJobIdsList()):
            stopWatch.start()
            try:
                job = mysql.fetchOne(QRY_FIND_JOB_FOR_ENRICHMENT, id)
                if job is None:
                    print(f'Job id={id} not found in database, skipping')
                    continue
                title = job[1]
                company = job[3]
                printHR()
                now = str(datetime.datetime.now())
                print(yellow(f'Job {idx+1}/{total} Started at: {now} ->',
                             f' id={id}, title={title}, company={company}'))
                # DB markdown blob decoding
                markdown = removeExtraEmptyLines(job[2].decode("utf-8"))
                crewOutput: CrewOutput = crew.kickoff(
                    inputs={"markdown": f'# {title} \n {markdown}'})
                result: dict[str, str] = rawToJson(crewOutput.raw)
                if result is not None:
                    validateResult(result)
                    mysql.updateFromAI(id, company, result, 'technologies')
            except openai.APIStatusError as e:
                jobErrors.add((id, f'{title} - {company}: {e}'))
                raise e
            except Exception as ex:
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
            stopWatch.end()
            print(yellow(f'Total processed jobs: {idx+1}/{total}'))
            print()
            print()
        if jobErrors:
            print(red(f'Total job errors: {len(jobErrors)}'))
            [print(yellow(f'{e[0]} - {e[1]}')) for e in jobErrors]


def getJobIdsList() -> list[int]:
    jobIds = [row[0]
              for row in mysql.fetchAll(QRY_FIND_JOBS_IDS_FOR_ENRICHMENT)]
    print(yellow(f'{jobIds}'))
    return jobIds


def rawToJson(raw: str) -> dict[str, str]:
    # FIXME: unit test this fnc & all regex code
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
#     res = re.sub('\\\\u00ai', '\u00ad', res)  # á
#     res = re.sub('\\\\u00f3', '\u00ed', res)  # í
#     res = re.sub('\\\\u00f3', '\u00ed', res)  # í
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
                result.update(
                    {'salary': re.sub(regex, r'\2', salary, flags=re.I)})
    listsToString(result, ['required_technologies', 'optional_technologies'])


def listsToString(result: dict[str, str], fields: list[str]):
    for f in fields:
        value = result.get(f, None)
        if not value:
            result[f] = None
        elif isinstance(value, list):
            result[f] = ','.join(value)


@CrewBase
class AiJobSearch:

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher_agent(self) -> Agent:
        timeout = getEnv(AI_ENRICHMENT_JOB_TIMEOUT_MINUTES)
        print('Creating agent:',
              f'timeout (minutes)={timeout}')
        config = self.agents_config['researcher_agent']
        result = Agent(
            llm=LLM_CFG,
            config=config,
            result_as_answer=True,
            verbose=True,
            max_iter=1,
            # max_rpm=1,
            max_execution_time=timeout * 60)
        return result

    @task
    def researcher_task(self) -> Task:
        print('Creating task')
        config = self.tasks_config['researcher']
        return Task(config=config,
                    verbose=True)
        # ,output_json=JobTaskOutputModel

    @crew
    def crew(self) -> Crew:
        """Creates the AiJobSearch crew"""
        print('Creating the AiJobSearch crew')
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            # response_format:
            verbose=True,
        )
