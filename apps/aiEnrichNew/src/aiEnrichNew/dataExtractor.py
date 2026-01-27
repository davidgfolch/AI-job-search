import json
from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import emptyToNone, maxLen
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import magenta, printHR, yellow, cyan, red
from commonlib.environmentUtil import getEnv
from commonlib.ai_helpers import footer, mapJob, printJob, validateResult, rawToJson, RETRY_ERROR_PREFIX, MAX_AI_ENRICH_ERROR_LEN
from commonlib.aiEnrichRepository import AiEnrichRepository
from .llm_client import get_pipeline
import traceback

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


stopWatch = StopWatch()
totalCount = 0
jobErrors = set[tuple[int, str]]()

def dataExtractor() -> int:
    global totalCount, jobErrors
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        total = repo.count_pending_enrichment()
        if total == 0:
            return total
        print()
        print(f'{total} jobs to be ai_enriched...')
        # Ensure model is loaded
        print(cyan(f"System Prompt:\n{SYSTEM_PROMPT}"))
        pipe = get_pipeline()
        for idx, id in enumerate(_getJobIdsList(repo)):
            _process_job_safe(repo, pipe, id, total, idx, "enrich")
        return total
    
def retry_failed_jobs() -> int:
    with MysqlUtil() as mysql:
        repo = AiEnrichRepository(mysql)
        # Fetch one failed job
        error_id = repo.get_enrichment_error_id_retry()
        if error_id is None:
            return 0
        pipe = get_pipeline()
        printHR(yellow)
        print(yellow(f"Retrying failed job id={error_id}..."))
        _process_job_safe(repo, pipe, error_id, 1, 0, "retry")
        return 1


def _process_job_safe(repo: AiEnrichRepository, pipe, id: int, total: int, idx: int, process_name: str):
    global totalCount, jobErrors
    printHR(yellow)
    stopWatch.start()
    title, company = "Unknown", "Unknown"
    try:
        job = repo.get_job_to_enrich(id) if process_name == "enrich" else repo.get_job_to_retry(id)
        if job is None:
            print(f'Job id={id} not found in database, skipping')
            return  # Will hit finally/end of func
        title, company, markdown = mapJob(job)
        printJob(process_name, total, idx, id, title, company, len(markdown))
        result = extract_job_data(pipe, title, markdown)
        print('Result:\n', magenta(json.dumps(result, indent=2)))
        if result is not None:
            _save(repo, id, company, result)
    except (Exception, KeyboardInterrupt) as ex:
        _handle_error(repo, id, title, company, ex, process_name)
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


def _save(repo: AiEnrichRepository, id, company, result: dict):
    validateResult(result)
    repo.update_enrichment(id, 
                           result.get('salary', None), 
                           result.get('required_technologies', None),
                           result.get('optional_technologies', None))

def _handle_error(repo: AiEnrichRepository, id, title, company, ex, process_name):
    print(red(traceback.format_exc()))
    jobErrors.add((id, f'{title} - {company}: {ex}'))
    prefix = RETRY_ERROR_PREFIX if process_name == "retry" else ""
    error_msg = f"{prefix}{ex}"
    if repo.update_enrichment_error(id, error_msg, True) == 0:
        print(red(f"could not update ai_enrich_error, id={id}"))
    else:
        print(yellow(f"ai_enrich_error set, id={id}"))

def _getJobIdsList(repo: AiEnrichRepository) -> list[int]:
    jobIds = repo.get_pending_enrichment_ids()
    print(yellow(f'{jobIds}'))
    return jobIds
