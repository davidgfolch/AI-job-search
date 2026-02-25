from commonlib.environmentUtil import getEnv

def get_job_system_prompt() -> str:
    return """You are an expert at analyzing job offers.
Extract the following information from the job offer below and return it as a valid JSON object:
- required_technologies: A string with comma-separated list of required technologies. Keep it concise.
- optional_technologies: A string with comma-separated list of optional/nice-to-have technologies. Keep it concise.
- salary: The salary information as a single string (e.g. "80k-90k" or "120000 USD") ONLY if explicitly stated in the text. If not found, return null. DO NOT guess or invent a salary.
- modality: The work modality. Must be exactly REMOTE, HYBRID, or ON_SITE. If not explicitly found, try to infer it from context or return null.

Format your response as a single valid JSON object strictly complying with this structure:
{
  "required_technologies": "tech1, tech2",
  "optional_technologies": "tech3",
  "salary": null,
  "modality": "REMOTE"
}
Strictly JSON. No conversational text. No markdown blocks."""

def get_skill_system_prompt() -> str:
    categories = getEnv("AI_SKILL_CATEGORIES", required=True)
    return f"""You are an expert technical recruiter and software engineer.
Your task is to provide a structured description for a given technical skill.
The structure MUST be:
1. **Summary**: A concise 1-2 sentence overview of what the skill is.
2. **Deep Technical Details**: A detailed explanation including:
   - Core Functionality
   - Usage Types (library, framework, etc.)
   - Key Modules/Components
   - Integration with co-occurring technologies
3. **Category**: One or more of [{categories}] (comma separated).
Output ONLY the structured text. Do not include any conversational text. Use 'Category: ' prefix for the category line."""

def get_batch_size() -> int:
    return int(getEnv('AI_BATCH_SIZE', '10'))

def get_input_max_len() -> int:
    return int(getEnv('AI_INPUT_MAX_LEN', '12000'))

def get_enrich_timeout_job() -> float:
    return float(getEnv('AI_ENRICH_TIMEOUT_JOB', 90))

def get_enrich_timeout_skill() -> float:
    return float(getEnv('AI_ENRICH_TIMEOUT_SKILL', 90))

def should_cleanup_gpu() -> bool:
    return getEnv('AI_ENRICH_GPU_CLEANUP', 'True') == 'True'
