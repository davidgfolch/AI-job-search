from commonlib.environmentUtil import getEnv, getEnvBool


def get_job_enabled() -> bool:
    return getEnvBool("AI_ENRICHNEW_JOB", True)


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


def get_batch_size() -> int:
    return int(getEnv("AI_ENRICHNEW_BATCH_SIZE", "10"))


def get_input_max_len() -> int:
    return int(getEnv("AI_ENRICHNEW_INPUT_MAX_LEN", "12000"))


def get_enrich_timeout_job() -> float:
    return float(getEnv("AI_ENRICHNEW_TIMEOUT_JOB", 90))


def should_cleanup_gpu() -> bool:
    return getEnv("AI_ENRICHNEW_GPU_CLEANUP", "True") == "True"
