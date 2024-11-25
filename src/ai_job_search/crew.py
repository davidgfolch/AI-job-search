import json
import re
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.flow.flow import Flow, start
from crewai.crews.crew_output import CrewOutput
from ai_job_search.terminalColor import red, yellow
from ai_job_search.tools.mysqlUtil import MysqlUtil


LLM_CONFIG = LLM(model="ollama/llama3.2",
                 base_url="http://localhost:11434",
                 temperature=0)


class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        try:
            mysqlUtil = MysqlUtil()
            crew = AiJobSearch().crew()
            for job in mysqlUtil.getJobsForAiEnrichment():
                id = job[0]
                title = job[1]
                company = job[3]
                markdown = re.sub(r'( *\n){2,}', '\n',
                                  # DB markdown blob decoding
                                  job[2].decode("utf-8"),
                                  re.MULTILINE)
                crew_output: CrewOutput = crew.kickoff(inputs={
                    "markdown": f'# {title} \n {markdown}',
                })
                # if crew_output.json_dict:
                #   json.dumps(crew_output.json_dict)
                # if crew_output.pydantic:
                #     crew_output.pydantic

                # TODO: Version crew_output.json_dict hace que el agente
                # piense demasiado, mas AI, más lento, en la Task hay que
                # poner output_json=JobTaskOutputModel
                # FIXME: relocation AI NO funciona bien
                result: dict[str, str] = rawToJson(crew_output.raw)
                if result is not None:
                    validateResult(result)
                    mysqlUtil.updateFromAI(id, company, result)
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


def rawToJson(raw) -> dict[str, str]:
    try:
        IM = re.I | re.M
        # remove invalid scapes
        raw = re.sub(r'\\([#&-|])', r'\1', raw, flags=re.M)
        # remove Agent Thought
        raw = re.sub(r'\nThought:(.*\n)*', '', raw, flags=IM)
        # remove json prefix
        raw = re.sub(r'json *object *', '', raw, flags=IM)
        raw = re.sub(r'("relocation": *)(\d+)', r'\1"\2"', raw, flags=IM)
        raw = re.sub(r'("relocation": *)(true)', r'\1"1"', raw, flags=IM)
        raw = re.sub(r'("relocation": *)(false)', r'\1"0"', raw, flags=IM)
        return dict(json.loads(f'{raw}'))
    except Exception as ex:
        print(red('Error: could not parse raw as json: ',
                  f'{ex} in json -> {raw}'))
        return None


def validateResult(result: dict[str, str]):
    relocation = result.get('relocation', 0)
    if re.match('.*relocation.*', relocation, re.I):
        result['relocation'] = 1
    elif relocation != 1:
        result['relocation'] = 0
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
            llm=LLM_CONFIG,
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
            verbose=True,
        )
