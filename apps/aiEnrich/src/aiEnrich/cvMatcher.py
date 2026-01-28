import json
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.crews.crew_output import CrewOutput

from commonlib.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import cyan, printHR, yellow, red
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.ai_helpers import combineTaskResults, footer, mapJob, printJob, validateResult
from commonlib.cv_loader import CVLoader
from commonlib.aiEnrichRepository import AiEnrichRepository
import traceback

VERBOSE = False
DEBUG = False

LLM_CFG = LLM(
    # model="ollama/gemma3",
    model="ollama/llama3.2",
    # model="ollama/glm4",
    # model="ollama/granite4",
    # model="ollama/nuextract",  # hangs on local ollama
    # model="ollama/deepseek-r1:8b",  # no GPU inference
    base_url="http://localhost:11434",
    temperature=0)


mysql = None
stopWatch = StopWatch()
# global counter for total processed jobs across runs
totalCount = 0
total = 0
jobErrors = set[tuple[int, str]]()


def cvMatch() -> int:
    global totalCount, jobErrors
    cv_loader = CVLoader(cv_location=getEnv('CV_LOCATION', './cv/cv.txt'), enabled=getEnvBool('AI_CV_MATCH'))
    if not cv_loader.load_cv_content():
        return 0
    cvContent = cv_loader.get_content()
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        total = repo.count_pending_cv_match()
        if total == 0:
            return total
        crew: Crew = CVMatcher().crew()
        limit = int(getEnv('AI_CV_MATCH_LIMIT', '10'))
        jobIds = repo.get_pending_cv_match_ids(limit)
        print(yellow(f'{jobIds}'))
        for idx, id in enumerate(jobIds):
            printHR(yellow)
            stopWatch.start()
            title, company = "Unknown", "Unknown"
            try:
                job = repo.get_job_to_match_cv(id)
                if job is None:
                    print(f'Job id={id} not found regarding CV MATCH, skipping')
                    continue
                title, company, markdown = mapJob(job)
                printJob('CV match', total, idx, id, title, company, len(markdown) + (len(cvContent) if cvContent else 0))
                inputs = {"markdown": f'# {title} \n {markdown}', "cv_content": cvContent}
                crewOutput: CrewOutput = crew.kickoff(inputs=inputs)
                result = combineTaskResults(crewOutput, DEBUG)
                print('Result: ', cyan(json.dumps(result)))
                if result is not None:
                    _save(repo, id, result)
            except (Exception, KeyboardInterrupt) as ex:
                print(red(traceback.format_exc()))
                jobErrors.add((id, f'{title} - {company}: {ex}'))
                repo.update_enrichment_error(id, str(ex), False)
            totalCount += 1
            stopWatch.end()
            footer(total, idx, totalCount, jobErrors)
        return total


def _save(repo: AiEnrichRepository, id, result: dict):
    validateResult(result)
    repo.update_cv_match(id, result.get('cv_match_percentage', None))


@CrewBase
class CVMatcher:

    agents_config = 'config/cvMatcher/agents.yaml'
    tasks_config = 'config/cvMatcher/tasks.yaml'

    @agent
    def cv_matcher_agent(self) -> Agent:
        config = self.agents_config['cv_matcher_agent']
        return Agent(llm=LLM_CFG,
                     config=config,
                     result_as_answer=True,
                     verbose=VERBOSE,
                     max_iter=1,
                     respect_context_window=True,  # auto-manage context limits
                     max_execution_time=getEnv('AI_ENRICH_TIMEOUT_CV_MATCH'))

    @task
    def cv_matcher_task(self) -> Task:
        config = self.tasks_config['cv_matcher_task']
        return Task(config=config, verbose=VERBOSE)

    @crew
    def crew(self) -> Crew:
        agents = [self.cv_matcher_agent()]
        tasks = [self.cv_matcher_task()]
        return Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=VERBOSE)
