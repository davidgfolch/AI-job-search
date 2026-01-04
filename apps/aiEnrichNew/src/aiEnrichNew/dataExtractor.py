import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import emptyToNone, maxLen
from commonlib.stopWatch import StopWatch
from commonlib.terminalColor import magenta, printHR, yellow, cyan
from commonlib.util import getEnv
from .jsonHelper import footer, mapJob, printJob, saveError, validateResult, rawToJson

# Configuration
VERBOSE = True 
DEBUG = False
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

# Global pipeline instance
_PIPELINE = None

def get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        print(cyan(f"Loading local model: {MODEL_ID}..."))
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, 
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        _PIPELINE = pipeline(
            "text-generation", 
            model=model, 
            tokenizer=tokenizer, 
            max_new_tokens=1024, # Enough for JSON output
            temperature=0.1, # Low temp for deterministic extraction
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=False
        )
        print(cyan("Local model loaded."))
    return _PIPELINE

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
totalCount = 0
jobErrors = set[tuple[int, str]]()

def dataExtractor() -> int:
    global totalCount, jobErrors
    with MysqlUtil() as mysql:
        total = mysql.count(QRY_COUNT)
        if total == 0:
            return total
        print(f'{total} jobs to be ai_enriched...')
        
        # Ensure model is loaded
        pipe = get_pipeline()

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
                
                # Extract using local LLM
                result = extract_job_data(pipe, title, markdown)
                
                print('Result:\n', magenta(json.dumps(result, indent=2)))
                if result is not None:
                    save(mysql, id, company, result)
            except (Exception, KeyboardInterrupt) as ex:
                saveError(mysql, jobErrors, id, title, company, ex, True)
            totalCount += 1
            stopWatch.end()
            footer(total, idx, totalCount, jobErrors)
        return total

def extract_job_data(pipe, title, markdown) -> dict:
    """
    Constructs the prompt and extracts JSON from local LLM.
    """
    system_prompt = """You are an expert at analyzing job offers.
Extract the following information from the job offer below and return it as a valid JSON object:
- required_technologies: A string with comma-separated list of required technologies.
- optional_technologies: A string with comma-separated list of optional/nice-to-have technologies.
- salary: The salary information if available, otherwise null.

Format your response as a single valid JSON object strictly complying with this structure:
{
  "required_technologies": "tech1, tech2",
  "optional_technologies": "tech3",
  "salary": "50k-60k"
}
Do not include any conversational text, only the JSON."""

    user_message = f"Job Title: {title}\n\nDescription:\n{markdown}"
    
    messages = [
        {"role": "system", "content": system_prompt},
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
