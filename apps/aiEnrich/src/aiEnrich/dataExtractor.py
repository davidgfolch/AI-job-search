import json
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.crews.crew_output import CrewOutput

from commonlib.mysqlUtil import MysqlUtil
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import magenta, printHR, yellow
from commonlib.environmentUtil import getEnv
from commonlib.ai_helpers import combineTaskResults, footer, mapJob, printJob, saveError, validateResult
from commonlib.sqlUtil import maxLen, emptyToNone


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

QRY_FROM = """
FROM jobs
WHERE (ai_enriched IS NULL OR not ai_enriched) and
not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_COUNT = f"""SELECT count(id) {QRY_FROM}"""
QRY_FIND_IDS = f"""SELECT id {QRY_FROM}"""
QRY_FIND = """
SELECT id, title, markdown, company
FROM jobs
WHERE id=%s and not ai_enriched and not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_UPDATE = """
UPDATE jobs SET
    salary=%s,
    required_technologies=%s,
    optional_technologies=%s,
    ai_enriched=1
WHERE id=%s"""


stopWatch = StopWatch()
# global counter for total processed jobs across runs
totalCount = 0
total = 0
jobErrors = set[tuple[int, str]]()


def dataExtractor() -> int:
    global totalCount, jobErrors
    with MysqlUtil() as mysql:
        total = mysql.count(QRY_COUNT)
        if total == 0:
            return total
        print(f'{total} jobs to be ai_enriched...')
        crew: Crew = DataExtractor().crew()
        for idx, id in enumerate(getJobIdsList(mysql)):
            printHR(yellow)
            stopWatch.start()
            try:
                job = mysql.fetchOne(QRY_FIND, id)
                if job is None:
                    print(f'Job id={id} not found in database (or mark as ignored, discarded, closed) , skipping')
                    continue
                title, company, markdown = mapJob(job)
                printJob('enrich', total, idx, id, title, company, len(markdown))
                inputs = {"markdown": f'# {title} \n {markdown}'}
                crewOutput: CrewOutput = crew.kickoff(inputs=inputs)
                result = combineTaskResults(crewOutput, DEBUG)
                print('Result:\n', magenta(json.dumps(result, indent=2)))
                if result is not None:
                    save(mysql, id, company, result)
            except (Exception, KeyboardInterrupt) as ex:
                saveError(mysql, jobErrors, id, title, company, ex, True)
            totalCount += 1
            stopWatch.end()
            footer(total, idx, totalCount, jobErrors)
        return total

def save(mysql: MysqlUtil, id, company, result: dict):
    validateResult(result)
    params = maxLen(emptyToNone(
                        (result.get('salary', None),
                            result.get(f'required_technologies', None),
                            result.get(f'optional_technologies', None),
                            id)),
                        (200, 1000, 1000, None))  # TODO: get mysql DDL metadata varchar sizes
    mysql.updateFromAI(QRY_UPDATE, params)


@CrewBase
class DataExtractor:

    agents_config = 'config/dataExtractor/agents.yaml'
    tasks_config = 'config/dataExtractor/tasks.yaml'

    @agent
    def extractor_agent(self) -> Agent:
        config = self.agents_config['extractor_agent']
        result = Agent(llm=LLM_CFG,
                       config=config,
                       result_as_answer=True,
                       verbose=VERBOSE,
                       max_iter=1,
                       # max_rpm=1,
                       max_execution_time=getEnv('AI_ENRICH_EXTRACT_TIMEOUT_SECONDS'))
        return result

    @task
    def extractor_task(self) -> Task:
        config = self.tasks_config['extractor_task']
        return Task(config=config, verbose=VERBOSE)

    @crew
    def crew(self) -> Crew:
        agents = [self.extractor_agent()]
        tasks = [self.extractor_task()]
        return Crew(agents=agents,
                    tasks=tasks,
                    process=Process.sequential,
                    verbose=VERBOSE)


def getJobIdsList(mysql: MysqlUtil) -> list[int]:
    jobIds = [row[0] for row in mysql.fetchAll(QRY_FIND_IDS)]
    print(yellow(f'{jobIds}'))
    return jobIds
