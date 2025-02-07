import datetime
import json
import os
import re
import traceback
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.flow.flow import Flow, start
from crewai.crews.crew_output import CrewOutput
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import openai
from ai_job_search.tools import stopWatch
from ai_job_search.tools.terminalColor import printHR, red, yellow
from ai_job_search.tools.mysqlUtil import (
    QRY_COUNT_JOBS_FOR_ENRICHMENT, QRY_FIND_JOB_FOR_ENRICHMENT,
    QRY_FIND_JOBS_IDS_FOR_ENRICHMENT, MysqlUtil, updateFieldsQuery)
from ai_job_search.tools.util import hasLen, removeExtraEmptyLines

load_dotenv()
MAX_AI_ENRICH_ERROR_LEN = 500

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

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


class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        mysqlUtil = MysqlUtil()
        jobErrors = set[tuple[int, str]]()
        try:
            print('Getting job ids...')
            count = mysqlUtil.count(QRY_COUNT_JOBS_FOR_ENRICHMENT)
            if count == 0:
                return
            jobIds = [row[0] for row in mysqlUtil.fetchAll(
                QRY_FIND_JOBS_IDS_FOR_ENRICHMENT)]
            print(f'{count} jobs to be ai_enriched...')
            print(yellow(f'{jobIds}'))
            crew = AiJobSearch().crew()
            for idx, id in enumerate(jobIds):
                stopWatch.start()
                try:
                    job = mysqlUtil.fetchOne(QRY_FIND_JOB_FOR_ENRICHMENT, id)
                    if job is None:
                        print(f'Job id={id} not found in database, skipping')
                        continue
                    title = job[1]
                    company = job[3]
                    printHR()
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(
                        yellow(f'Job {idx+1}/{count} Started at: {now} ->',
                               f' id={id}, title={title}, company={company}'))
                    # DB markdown blob decoding
                    markdown = removeExtraEmptyLines(job[2].decode("utf-8"))
                    crewOutput: CrewOutput = crew.kickoff(
                        inputs={
                            "markdown": f'# {title} \n {markdown}',
                        })
                    # TODO: Version crew_output.json_dict hace que el agente
                    # piense demasiado, mas AI, más lento, en la Task hay que
                    # poner output_json=JobTaskOutputModel
                    # if crew_output.json_dict:
                    #   json.dumps(crew_output.json_dict)
                    # if crew_output.pydantic:
                    #     crew_output.pydantic
                    result: dict[str, str] = rawToJson(crewOutput.raw)
                    if result is not None:
                        validateResult(result)
                        mysqlUtil.updateFromAI(
                            id, company, result, 'technologies')
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
                    count = mysqlUtil.executeAndCommit(query, params)
                    if count == 0:
                        print(yellow(f"ai_enrich_error set, id={id}"))
                    else:
                        print(
                            red(f"could not update ai_enrich_error, id={id}"))

                stopWatch.end()
                print(yellow(f'Total processed jobs: {idx+1}/{count}'))
                print()
                print()

            if jobErrors:
                print(red(f'Total job errors: {len(jobErrors)}'))
                [print(yellow(f'{e[0]} - {e[1]}')) for e in jobErrors]
            print(yellow(''*60))
            print(yellow('ALL ROWS PROCESSES!'))
            print(yellow(''*60))
        finally:
            mysqlUtil.close()

    # @router(generate_shakespeare_x_post)
    # def evaluate_x_post(self):
    #     if self.state.retry_count > 3:
    #         return "max_retry_exceeded"
    #     result = XPostReviewCrew().crew().kickoff(
    # inputs={"x_post": self.state.x_post})
    #     self.state.valid = result["valid"]
    #     self.state.feedback = result["feedback"]
    #     print("valid", self.state.valid)
    #     print("feedback", self.state.feedback)
    #     self.state.retry_count += 1
    #     if self.state.valid:
    #         return "complete"
    #     return "retry"


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
        res = fixInvalidUnicode(res)
        return dict(json.loads(f'{res}'))
    except json.JSONDecodeError as ex:
        if idx := ex.msg.find('Invalid \\uXXXX escape:') > -1:
            try:
                res = res[0:idx-1]
                res += re.sub(r'\\(u[0-9a-fA-F]{4})', '\\\\\1', res[idx:idx+6])
                if len(res) > idx+6:
                    res += res[idx+7:len(res)-1]
                print(yellow(f'Replaced invalid unicode\'s in json:\n{res}'))
                return dict(json.loads(f'{res}'))
            except Exception as ex:
                printJsonException(ex)
                raise ex
        else:
            raise ex
    except Exception as ex:
        printJsonException(ex)
        raise ex


def printJsonException(ex: Exception, res: str, raw: str) -> None:
    print(red(traceback.format_exc()))
    print(red(f'Could not parse json after clean it: {ex}'))
    print(red(f'Json after clean:\n{res}'))
    print(yellow(f'Original json:\n{raw}'))
    raise ex


def fixInvalidUnicode(res):
    # fix invalid unicode
    res = re.sub('\\\\u00ai', '\u00ad', res)  # á
    res = re.sub('\\\\u00f3', '\u00ed', res)  # í
    res = re.sub('\\\\u00f3', '\u00ed', res)  # í
    return res


def fixJsonInvalidAttribute(raw):
    """Fixes LLM invalid json value, f.ex.:
    "salary": "xx" + "yy",
    "salary": "xx",",
    """
    raw = re.sub(r'" \+ "', ' + ', raw)
    # {"salary": "$\text{Salary determined by the market and your experience} \\\$",
    raw = re.sub(r'"[$]\\text\{([^\}]+)\} \\\\\\\$"', r'\1', raw)
    return re.sub(r'(.+)",",', r'\1",', raw)


def fixJsonEndCurlyBraces(raw):
    raw = re.sub('"[)\\\\]', '"}', raw)
    idx = raw.rfind('}')
    if idx > 0 and idx + 1 < len(raw):
        # remove extra text after }
        return raw[0:idx+1]
    if idx == -1:
        # sometimes LLM forgets to close }
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
        if salary == 'Salario no disponible':
            result.update({'salary': None})
        elif hasLen(
                re.finditer(regex := r'^(sueldo|salarios?)[: ]+(.+)',
                            salary, flags=re.I)):
            result.update({'salary': re.sub(regex, r'\2', salary, flags=re.I)})
    opTechs = result.get('optional_technologies', None)
    if not opTechs:
        result['optional_technologies'] = None


@CrewBase
class AiJobSearch:

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher_agent(self) -> Agent:
        print('Creating agent')
        config = self.agents_config['researcher_agent']
        result = Agent(
            llm=LLM_CFG,
            config=config,
            result_as_answer=True,
            verbose=False)
        return result

    @task
    def researcher_task(self) -> Task:
        print('Creating task')
        config = self.tasks_config['researcher']
        return Task(config=config)
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
