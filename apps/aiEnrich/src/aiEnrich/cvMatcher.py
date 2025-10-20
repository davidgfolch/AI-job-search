import json
import traceback
from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.crews.crew_output import CrewOutput
import pandas as pd
import pdfplumber
from pathlib import Path

from .crewHelper import combineTaskResults, footer, mapJob, printJob, saveError, validateResult
from commonlib.mysqlUtil import MysqlUtil, emptyToNone, maxLen
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import cyan, printHR, red, yellow
from commonlib.util import getEnv, getEnvBool

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
WHERE cv_match_percentage is null and not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_COUNT = f"""SELECT count(id) {QRY_FROM}"""
QRY_FIND_IDS = f"""SELECT id {QRY_FROM} LIMIT {getEnv('AI_CV_MATCH_LIMIT', '10')}"""
QRY_FIND = f"""
SELECT id, title, markdown, company
FROM jobs
WHERE id=%s and cv_match_percentage is null and not (ignored or discarded or closed)
ORDER BY created desc 
"""
QRY_UPDATE = """UPDATE jobs SET cv_match_percentage=%s WHERE id=%s"""

# CV content cache
cvContent = None
mysql = None
stopWatch = StopWatch()
# global counter for total processed jobs across runs
totalCount = 0
total = 0
jobErrors = set[tuple[int, str]]()


def cvMatch() -> int:
    global totalCount, jobErrors
    if not getEnvBool('AI_CV_MATCH'):
        return 0
    if not loadCVContent():  # Load CV once at startup if matching is enabled
        return 0
    with MysqlUtil() as mysql:
        total = mysql.count(QRY_COUNT)
        if total == 0:
            return total
        crew: Crew = CVMatcher().crew()
        for idx, id in enumerate(getJobIdsList(mysql)):
            printHR(yellow)
            stopWatch.start()
            try:
                job = mysql.fetchOne(QRY_FIND, id)
                if job is None:
                    print(f'Job id={id} not found in database (or mark as ignored, discarded, closed) , skipping')
                    continue
                title, company, markdown = mapJob(job)
                printJob('CV match', total, idx, id, title, company, len(markdown)+len(cvContent))
                inputs = {"markdown": f'# {title} \n {markdown}', "cv_content": cvContent}
                crewOutput: CrewOutput = crew.kickoff(inputs=inputs)
                result = combineTaskResults(crewOutput, DEBUG)
                print('Result: ', cyan(json.dumps(result)))
                if result is not None:
                    save(mysql, id, result)
            except (Exception, KeyboardInterrupt) as ex:
                saveError(mysql, jobErrors, id, title, company, ex, False)
            totalCount += 1
            stopWatch.end()
            footer(total, idx, totalCount, jobErrors)
        return total


def save(mysql: MysqlUtil, id, result: dict):
    validateResult(result)
    params = maxLen(emptyToNone((result.get('cv_match_percentage', None), id)), (None, None))
    mysql.updateFromAI(QRY_UPDATE, params)


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
                     max_execution_time=getEnv('AI_ENRICH_CV_MATCH_TIMEOUT_SECONDS'))

    @task
    def cv_matcher_task(self) -> Task:
        config = self.tasks_config['cv_matcher_task']
        return Task(config=config, verbose=VERBOSE)

    @crew
    def crew(self) -> Crew:
        agents = [self.cv_matcher_agent()]
        tasks = [self.cv_matcher_task()]
        return Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=VERBOSE)


def getJobIdsList(mysql: MysqlUtil) -> list[int]:
    jobIds = [row[0] for row in mysql.fetchAll(QRY_FIND_IDS)]
    print(yellow(f'{jobIds}'))
    return jobIds


def extractTextFromPDF(pdf_path: str) -> str:
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text.append(page_text)
            # Extraer tablas y convertirlas a Markdown
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                markdown = df.to_markdown(index=False)
                all_text.append(markdown)
    # Unir todo el contenido en una sola cadena Markdown
    return "\n\n".join(all_text)


def loadCVContent():
    global cvContent
    if not getEnvBool('AI_CV_MATCH'):
        print(yellow('AI_CV_MATCH disabled'))
        return
    if cvContent is not None:
        return True
    cvLocation = getEnv('AI_CV_MATCH_LOCATION')
    print(yellow(f'Loading CV from: {cvLocation}'))
    if not (cvLocation.endswith('.pdf') or cvLocation.endswith('.txt')):
        print(yellow('AI_CV_MATCH is enabled but AI_CV_MATCH_LOCATION is not set, allowed formats: .txt, .pdf'))
        return False
    try:
        filePath = Path(cvLocation)
        cvLocationTxt = cvLocation.replace('.pdf', '.txt')
        filePathTxt = Path(cvLocationTxt)
        if not filePath.exists() and not filePathTxt.exists():
            print(red(f'CV file not found: {cvLocation}'))
            return False
        fileExtension = filePath.suffix.lower()
        if fileExtension == '.pdf' and not filePathTxt.exists():
            cvContent = extractTextFromPDF(cvLocation)
            print(yellow(f'CV (PDF) loaded from: {cvLocation} ({len(cvContent)} chars)'))
            with open(cvLocationTxt, 'w', encoding='utf-8') as mdFile:
                mdFile.write(cvContent)
        elif filePathTxt.exists():
            with open(cvLocationTxt, 'r', encoding='utf-8') as f:
                cvContent = f.read()
            print(yellow(f'CV (text from PDF) loaded from: {cvLocationTxt} ({len(cvContent)} chars)'))
        # elif fileExtension in ['.txt', '.md', '.markdown']:
        #     with open(cvLocation, 'r', encoding='utf-8') as f:
        #         cvContent = f.read()
        #     print(yellow(f'CV (text) loaded from: {cvLocation} ({len(cvContent)} chars)'))
        else:
            print(red(f'Unsupported CV file format: {fileExtension}. Supported formats: .txt, .pdf'))
            return False
        if not cvContent or len(cvContent.strip()) == 0:
            print(red('CV file is empty'))
            return False
        return True
    except FileNotFoundError:
        print(red(f'CV file not found: {cvLocation}'))
        return False
    except Exception as ex:
        print(red(f'Error loading CV: {ex}'))
        traceback.print_exc()
        return False
