import json
import re
import traceback
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.flow.flow import Flow, start
from crewai.crews.crew_output import CrewOutput
from ai_job_search.tools.terminalColor import red, yellow
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery


LLM_CONFIG = LLM(model="ollama/llama3.2",
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
                try:
                    id = job[0]
                    title = job[1]
                    company = job[3]
                    markdown = re.sub(r'(\s*(\n|\n\r|\r\n|\r)){2,}', '\n\n',
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
                    # TODO: check ai_enrichment error and flag into database with enrichment error
                    # try:
                    result: dict[str, str] = rawToJson(crew_output.raw)
                    if result is not None:
                        validateResult(result)
                        mysqlUtil.updateFromAI(id, company, result)
                except Exception as ex:
                    print(red(traceback.format_exc()))
                    print(yellow("Skipping! (ai_enrich_error set in DB)"))
                    MAX_AI_ENRICH_ERROR = 500
                    params = {'ai_enrich_error': str(ex)[:MAX_AI_ENRICH_ERROR],
                              'ai_enriched': True}
                    query, params = updateFieldsQuery([id], params)
                    mysqlUtil.executeAndCommit(query, params)
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
        # remove invalid scapes
        # TODO: REMOVE OR CHANGE UNICODE \u00f3
        raw = raw.replace('\$', '$')  # dont remove \$ ignore the warning
        raw = re.sub(r'[\\]+([`#&->_|])', r'\1', raw, flags=re.M)
        # replace " inside json values
        # TODO: raw = re.sub(r' *".+": *"(.+)" *(, *|\})', r'\1', raw, flags=re.M)
        # remove Agent Thought or Note
        raw = re.sub(r'\n(Thought|Note):(.*\n)*', '', raw, flags=IM)
        # remove json prefix
        raw = re.sub(r'json *object *', '', raw, flags=IM)
        raw = re.sub(r'(```)', '', raw, flags=IM)
        raw = re.sub(r'[*]+(.+)', r'\1', raw)
        lastCurlyBracesIdx = raw.rfind('}')
        if lastCurlyBracesIdx > 0 and lastCurlyBracesIdx + 1 < len(raw):
            raw = raw[0:lastCurlyBracesIdx+1]
        elif lastCurlyBracesIdx == -1:  # sometimes LLM forgets to close }
            raw += '}'
        return dict(json.loads(f'{raw}'))
    except Exception as ex:
        msg = f'Error info: could not parse raw as json: {ex} in json -> {raw}'
        print(red(msg))


def validateResult(result: dict[str, str]):
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
            # response_format:
            verbose=True,
        )
