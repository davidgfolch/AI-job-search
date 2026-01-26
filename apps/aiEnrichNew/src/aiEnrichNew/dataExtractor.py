import json
from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import emptyToNone, maxLen
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import magenta, printHR, yellow, cyan
from commonlib.environmentUtil import getEnv
from commonlib.ai_helpers import footer, mapJob, printJob, saveError, validateResult, rawToJson
from .llm_client import get_pipeline

# Configuration
VERBOSE = True 
DEBUG = False
# MODEL_ID moved to llm_client.py
SYSTEM_PROMPT = """You are an expert at analyzing job offers.
Extract the following information from the job offer below and return it as a valid JSON object:
- required_technologies: A string with comma-separated list of required technologies. Keep it concise.
- optional_technologies: A string with comma-separated list of optional/nice-to-have technologies. Keep it concise.
- salary: The salary information as a single string (e.g. "80k-90k" or "120000 USD") ONLY if explicitly stated in the text. If not found, return null. DO NOT guess or invent a salary.

Format your response as a single valid JSON object strictly complying with this structure:
{
  "required_technologies": "tech1, tech2",
  "optional_technologies": "tech3",
  "salary": null
}
Strictly JSON. No conversational text. No markdown blocks."""

QRY_FIND = """
SELECT id, title, markdown, company
FROM jobs
WHERE id=%s and not ai_enriched and not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_FROM = """
FROM jobs
WHERE (ai_enriched IS NULL OR not ai_enriched) and
not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_FIND_IDS = f"""SELECT id {QRY_FROM}"""
QRY_COUNT = f"""SELECT count(id) {QRY_FROM}"""
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
totalCount = 0
jobErrors = set[tuple[int, str]]()

def dataExtractor() -> int:
    global totalCount, jobErrors
    with MysqlUtil() as mysql:
        total = mysql.count(QRY_COUNT)
        if total == 0:
            return total
        
        print()
        print(f'{total} jobs to be ai_enriched...')
        # Ensure model is loaded
        print(cyan(f"System Prompt:\n{SYSTEM_PROMPT}"))
        pipe = get_pipeline()

        for idx, id in enumerate(getJobIdsList(mysql)):
            _process_job_safe(mysql, pipe, id, total, idx, QRY_FIND, "enrich")

        return total
    
def retry_failed_jobs() -> int:
    with MysqlUtil() as mysql:
        # Fetch one failed job
        rows = mysql.fetchAll(QRY_FIND_ERROR_ID)
        if not rows:
            return 0

        error_id = rows[0][0]
        pipe = get_pipeline()
        printHR(yellow)
        print(yellow(f"Retrying failed job id={error_id}..."))
        
        _process_job_safe(mysql, pipe, error_id, 1, 0, QRY_FIND_RETRY, "retry")
        return 1


def _process_job_safe(mysql: MysqlUtil, pipe, id: int, total: int, idx: int, query_find: str, process_name: str):
    global totalCount, jobErrors
    printHR(yellow)
    stopWatch.start()
    try:
        job = mysql.fetchOne(query_find, id)
        if job is None:
            print(f'Job id={id} not found in database, skipping')
            return  # Will hit finally/end of func

        title, company, markdown = mapJob(job)
        printJob(process_name, total, idx, id, title, company, len(markdown))
        
        result = extract_job_data(pipe, title, markdown)
        print('Result:\n', magenta(json.dumps(result, indent=2)))
        
        if result is not None:
            save(mysql, id, company, result)
            
    except (Exception, KeyboardInterrupt) as ex:
        # We need title/company for saveError? 
        # Variable scoping in python: title, company might not be defined if fetchOne fails or mapJob fails.
        # But if exceptions happen there, we catch them.
        # But saveError expects title, company.
        # We should init them to 'Unknown' or something?
        # Or just rely on Python's scoping if assigned.
        # To be safe:
        err_title = locals().get('title', 'Unknown Title')
        err_company = locals().get('company', 'Unknown Company')
        saveError(mysql, jobErrors, id, err_title, err_company, ex, True)
    
    totalCount += 1
    stopWatch.end()
    footer(total, idx, totalCount, jobErrors)

def extract_job_data(pipe, title, markdown) -> dict:
    user_message = f"Job Title: {title}\n\nDescription:\n{markdown}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    # Apply chat template
    prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    output = pipe(prompt)
    generated_text = output[0]['generated_text']
    if DEBUG:
         print(yellow(f"Raw LLM Output: {generated_text}"))
    return rawToJson(generated_text)


def save(mysql: MysqlUtil, id, company, result: dict):
    validateResult(result)
    params = maxLen(emptyToNone(
                        (result.get('salary', None),
                            result.get(f'required_technologies', None),
                            result.get(f'optional_technologies', None),
                            id)),
                        (200, 1000, 1000, None))
    mysql.updateFromAI(QRY_UPDATE, params)

def getJobIdsList(mysql: MysqlUtil) -> list[int]:
    jobIds = [row[0] for row in mysql.fetchAll(QRY_FIND_IDS)]
    print(yellow(f'{jobIds}'))
    return jobIds
