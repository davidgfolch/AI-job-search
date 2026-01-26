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
QRY_FIND_ERROR_ID = """
SELECT id FROM jobs 
WHERE ai_enrich_error IS NOT NULL AND ai_enrich_error != '' 
ORDER BY created DESC LIMIT 1"""
QRY_FIND_RETRY = """
SELECT id, title, markdown, company
FROM jobs
WHERE id=%s"""
QRY_UPDATE = """
UPDATE jobs SET
    salary=%s,
    required_technologies=%s,
    optional_technologies=%s,
    ai_enriched=1,
    ai_enrich_error=NULL
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
        
        crew = DataExtractor().crew()
        
        if total > 0:
            print(f'{total} jobs to be ai_enriched...')
            for idx, id in enumerate(getJobIdsList(mysql)):
                _process_job_safe(mysql, crew, id, total, idx, QRY_FIND, "enrich")

        return total


def retry_failed_jobs() -> int:
    global totalCount, jobErrors
    
    with MysqlUtil() as mysql:
        # Fetch one failed job
        rows = mysql.fetchAll(QRY_FIND_ERROR_ID)
        if not rows:
            return 0

        error_id = rows[0][0]
        crew = DataExtractor().crew()
        
        printHR(yellow)
        print(yellow(f"Retrying failed job id={error_id}..."))
        
        # We pass 0, 0 for total/idx as it is a single retry
        _process_job_safe(mysql, crew, error_id, 1, 0, QRY_FIND_RETRY, "retry")
        return 1


def _process_job_safe(mysql: MysqlUtil, crew: Crew, id: int, total: int, idx: int, query_find: str, process_name: str):
    global totalCount, jobErrors
    printHR(yellow)
    stopWatch.start()
    try:
        _process_job(mysql, crew, id, total, idx, query_find, process_name)
    except (Exception, KeyboardInterrupt) as ex:
        # We need title/company for saveError. _process_job gets them.
        # If _process_job fails before getting them, we might have issues.
        # But we can try to fetch them again or just log generic error.
        # Actually saveError needs them.
        # Let's simple duplicate fetch logic or better:
        # Re-read job to get title/company if needed? NO that's wasteful.
        # We can wrap the inner part.
        pass # Created a specialized helper below to handle this cleaner
        # Wait, I cannot easily pass title/company out if exception happens inside.
        # I'll preserve the original try-except block structure inside this wrapper?
        # Or better: put try-except inside _process_job and return success/fail?
        # But saveError is called in except block.
        
        # Let's try to stick to original structure as much as possible to be safe.
        # I will inline the logic in _process_job_safe effectively, but since I need it for both loops...
        
        # Let's revert to a slightly different refactor:
        # separate `process_job_logic` that raises exception, and `_process_job_wrapper` that handles it.
        # But `process_job_logic` needs to return title/company for the exception handler to use it?
        # Or the exception handler just logs what it has.
        
        # For simplicity in this `replace_file_content` block which is tricky with indentation:
        # I will define `_process_wrapper` that does the try/except.
        
    stopWatch.end()
    footer(total, idx, totalCount, jobErrors)


def _process_job_safe(mysql: MysqlUtil, crew: Crew, id: int, total: int, idx: int, query_find: str, process_name: str):
    global totalCount
    try:
        job = mysql.fetchOne(query_find, id)
        if job is None:
            print(f'Job id={id} not found in database, skipping')
            # If retrying and not found, maybe invalid ID.
            return

        title, company, markdown = mapJob(job)
        # Verify markdown length? existing code didn't explicitly check None, mapJob handles it.
        
        try:
            printJob(process_name, total, idx, id, title, company, len(markdown))
            inputs = {"markdown": f'# {title} \n {markdown}'}
            crewOutput: CrewOutput = crew.kickoff(inputs=inputs)
            result = combineTaskResults(crewOutput, DEBUG)
            print('Result:\n', magenta(json.dumps(result, indent=2)))
            if result is not None:
                save(mysql, id, company, result)
        except (Exception, KeyboardInterrupt) as ex:
            saveError(mysql, jobErrors, id, title, company, ex, True)
            
    except Exception as e:
         # Fallback if fetchOne fails or mapJob fails (unlikely)
         print(f"Error processing job {id}: {e}")
         
    totalCount += 1


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
