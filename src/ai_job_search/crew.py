import json
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.flow.flow import Flow, start
from crewai.crews.crew_output import CrewOutput
from ai_job_search.crewai import cvMatcher
from ai_job_search.crewai.crewHelper import combineTaskResults, getJobIdsList, mapJob, printJob, rawToJson, saveError, validateResult
from ai_job_search.crewai.cvMatcher import loadCVContent
from ai_job_search.tools.stopWatch import StopWatch
from ai_job_search.tools.terminalColor import printHR, red, yellow
from ai_job_search.tools.mysqlUtil import (QRY_COUNT_JOBS_FOR_ENRICHMENT, QRY_FIND_JOB_FOR_ENRICHMENT, MysqlUtil)
from ai_job_search.tools.util import (getEnv, consoleTimer, getEnvBool)

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


class AiJobSearchFlow(Flow):  # https://docs.crewai.com/concepts/flows
    """AiJobSearch crew"""

    @start()
    def processRows(self):
        global mysql
        global total
        if getEnvBool('AI_CV_MATCH'):
            loadCVContent()  # Load CV once at startup if matching is enabled
        while True:
            with MysqlUtil() as mysql:
                total = mysql.count(QRY_COUNT_JOBS_FOR_ENRICHMENT)
                if total == 0:
                    consoleTimer("All jobs are already AI enriched, ", '10s', end='\n')
                    continue
                print(f'{total} jobs to be ai_enriched...')
                self.enrichJobs(total)
                printHR(yellow)
                print(yellow('ALL ROWS PROCESSES!'))
                printHR(yellow)

    def enrichJobs(self, total):
        global totalCount, jobErrors
        crew: Crew = AiJobSearch().crew()
        for idx, id in enumerate(getJobIdsList(mysql)):
            printHR(yellow)
            stopWatch.start()
            try:
                job = mysql.fetchOne(QRY_FIND_JOB_FOR_ENRICHMENT, id)
                if job is None:
                    print(f'Job id={id} not found in database (or mark as ignored, discarded, closed) , skipping')
                    continue
                title, company, markdown = mapJob(job)
                printJob(total, idx, id, title, company)
                inputs = {"markdown": f'# {title} \n {markdown}'}
                if getEnvBool('AI_CV_MATCH'):
                    inputs["cv_content"] = cvMatcher.cvContent
                crewOutput: CrewOutput = crew.kickoff(inputs=inputs)
                result = combineTaskResults(crewOutput, DEBUG)
                print(f'AI Enrichment result:\n{json.dumps(result, indent=2)}')
                if result is not None:
                    validateResult(result)
                    mysql.updateFromAI(id, company, result)
            except (Exception, KeyboardInterrupt) as ex:
                saveError(mysql, jobErrors, id, title, company, ex)
            totalCount += 1
            stopWatch.end()
            print(yellow(f'Total processed jobs (this run): {idx+1}/{total}'))
            print(yellow(f'Global total processed jobs: {totalCount}'))
            print()
            print()
        if jobErrors:
            print(red(f'Total job errors: {len(jobErrors)}'))
            [print(yellow(f'{e[0]} - {e[1]}')) for e in jobErrors]


@CrewBase
class AiJobSearch:

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def extractor_agent(self) -> Agent:
        print('Creating extractor agent')
        config = self.agents_config['extractor_agent']
        result = Agent(
            llm=LLM_CFG,
            config=config,
            result_as_answer=True,
            verbose=VERBOSE,
            max_iter=1,
            # max_rpm=1,
            max_execution_time=getEnv('AI_ENRICH_EXTRACT_TIMEOUT_SECONDS'))
        return result

    @agent
    def cv_matcher_agent(self) -> Agent:
        """Agent for matching CV with job offer"""
        print('Creating cv_matcher_agent', '(Disabled)' if self.tasks_config.get('cv_matcher_agent', None) is None else '')
        config = self.agents_config['cv_matcher_agent']
        return Agent(llm=LLM_CFG,
                     config=config,
                     result_as_answer=True,
                     verbose=VERBOSE,
                     max_iter=1,
                     max_execution_time=getEnv('AI_ENRICH_CV_MATCH_TIMEOUT_SECONDS'))

    @task
    def extractor_task(self) -> Task:
        print('Creating extractor task')
        config = self.tasks_config['extractor_task']
        return Task(config=config, verbose=VERBOSE)

    # @task
    def cv_matcher_task(self) -> Task:
        """Task for matching CV with job offer"""
        # if self.tasks_config.get('cv_matcher_task', None) is None:
        if getEnvBool('AI_CV_MATCH') is False:
            print(yellow('CV matcher task not configured, skipping'))
            return None
        print('Creating cv_matcher_task')
        config = self.tasks_config['cv_matcher_task']
        return Task(config=config, verbose=VERBOSE)

    @crew
    def crew(self) -> Crew:
        """Creates the AiJobSearch crew"""
        print('Creating the AiJobSearch crew')
        agents = [self.extractor_agent()]
        tasks = [self.extractor_task()]
        # Add CV matcher if enabled
        cv_task = self.cv_matcher_task()
        if cv_task is not None:
            # cv_agent = self.cv_matcher_agent()
            # if cv_agent and cv_task:
            agents.append(self.cv_matcher_agent())
            tasks.append(cv_task)
            print(yellow('CV matching enabled'))
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=VERBOSE,
        )
