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
import litellm
from ai_job_search.tools import stopWatch
from ai_job_search.tools.terminalColor import printHR, red, yellow
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.tools.util import hasLen

load_dotenv()

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
    LLM_CFG = LLM(model="ollama/llama3.2",
                  base_url="http://localhost:11434",
                  temperature=0)


class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        mysqlUtil = MysqlUtil()
        try:
            crew = AiJobSearch().crew()
            for job in mysqlUtil.getJobsForAiEnrichment():
                stopWatch.start()
                try:
                    id = job[0]
                    title = job[1]
                    company = job[3]
                    printHR()
                    print(f'Job id={id}, title={title}, company={company}')
                    markdown = re.sub(r'(\s*(\n|\n\r|\r\n|\r)){3,}', '\n\n',
                                      # DB markdown blob decoding
                                      job[2].decode("utf-8"),
                                      re.MULTILINE)
                    crew_output: CrewOutput = crew.kickoff(
                        inputs={
                            "markdown": f'# {title} \n {markdown}',
                        })
                    # if crew_output.json_dict:
                    #   json.dumps(crew_output.json_dict)
                    # if crew_output.pydantic:
                    #     crew_output.pydantic
                    # TODO: Version crew_output.json_dict hace que el agente
                    # piense demasiado, mas AI, más lento, en la Task hay que
                    # poner output_json=JobTaskOutputModel
                    # TODO: TRY structured outputs with ollama or langchain?
                    # https://ollama.com/blog/structured-outputs
                    # https://python.langchain.com/docs/how_to/structured_output/
                    result: dict[str, str] = rawToJson(crew_output.raw)
                    if result is not None:
                        validateResult(result)
                        mysqlUtil.updateFromAI(id, company, result)
                except litellm.RateLimitError:
                    print(red(traceback.format_exc()))
                    print(yellow("RATE LIMIT ERROR!"))
                    exit(-1)
                except Exception as ex:
                    print(red(traceback.format_exc()))
                    print(yellow("Skipping! (ai_enrich_error set in DB)"))
                    MAX_AI_ENRICH_ERROR = 500
                    params = {'ai_enrich_error': str(ex)[:MAX_AI_ENRICH_ERROR],
                              'ai_enriched': True}
                    query, params = updateFieldsQuery([id], params)
                    mysqlUtil.executeAndCommit(query, params)
                stopWatch.end()
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
    try:
        IM = re.I | re.M
        # replace " inside json values
        # TODO:raw=re.sub(r' *".+": *"(.+)" *(, *|\})', r'\1', raw, flags=re.M)
        # remove Agent Thought or Note
        raw = re.sub(r'\n(Thought|Note):(.*\n)*', '', raw, flags=IM)
        # remove json prefix
        raw = re.sub(r'json *object *', '', raw, flags=IM)
        raw = re.sub(r'(```)', '', raw, flags=IM)
        raw = re.sub(r'[*]+(.+)', r'\1', raw)
        raw = re.sub(r'(.+)",",', r'\1",', raw)
        raw = fixJsonEndCurlyBraces(raw)
        raw = fixJsonInvalidAttribute(raw)
        return dict(json.loads(f'{raw}'))
    except Exception as ex:
        msg = f'Error info: could not parse raw as json: {ex} in json -> {raw}'
        print(red(msg))


def fixJsonInvalidAttribute(raw):
    # fixes LLM invalid json
    # example: "salary": "£80,000–£100,000" + "significant equity",
    return re.sub(r'" \+ "', ' + ', raw)


def fixJsonEndCurlyBraces(raw):
    idx = raw.rfind('}')
    if idx > 0 and idx + 1 < len(raw):
        # remove extra text after }
        return raw[0:idx+1]
    if idx == -1:
        # sometimes LLM forgets to close }
        return raw + '}'
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
        config = self.agents_config['researcher_agent']
        result = Agent(
            llm=LLM_CFG,
            config=config,
            result_as_answer=True,
            verbose=False)
        return result

    @task
    def researcher_task(self) -> Task:
        config = self.tasks_config['researcher']
        return Task(config=config)
        # ,output_json=JobTaskOutputModel

    @crew
    def crew(self) -> Crew:
        """Creates the AiJobSearch crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            # response_format:
            verbose=True,
        )
