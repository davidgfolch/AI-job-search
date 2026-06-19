from commonlib.environmentUtil import getEnv, getEnvBool


def get_enabled() -> bool:
    return getEnvBool("AI_ENRICHSKILL_ENABLED", True)


def get_backend() -> str:
    return getEnv("AI_ENRICHSKILL_BACKEND", "ollama")


def get_ollama_model() -> str:
    return getEnv("AI_ENRICHSKILL_OLLAMA_MODEL", "ollama/qwen2.5:3b")


def get_ollama_base_url() -> str:
    return getEnv("AI_ENRICHSKILL_OLLAMA_BASE_URL", "http://localhost:11434")


def get_max_new_tokens() -> int:
    return int(getEnv("AI_ENRICHSKILL_MAX_NEW_TOKENS", "2048"))


def get_hf_model_id() -> str:
    return getEnv("AI_ENRICHSKILL_HF_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct")


def get_hf_temperature() -> float:
    return float(getEnv("AI_ENRICHSKILL_HF_TEMPERATURE", "0.1"))


def get_hf_top_p() -> float:
    return float(getEnv("AI_ENRICHSKILL_HF_TOP_P", "0.9"))


def get_hf_repetition_penalty() -> float:
    return float(getEnv("AI_ENRICHSKILL_HF_REPETITION_PENALTY", "1.1"))


def get_batch_size() -> int:
    return int(getEnv("AI_ENRICHSKILL_BATCH_SIZE", "10"))


def get_input_max_len() -> int:
    return int(getEnv("AI_ENRICHSKILL_INPUT_MAX_LEN", "12000"))


def get_timeout() -> float:
    return float(getEnv("AI_ENRICHSKILL_TIMEOUT", "90"))


def get_gpu_cleanup() -> bool:
    return getEnv("AI_ENRICHSKILL_GPU_CLEANUP", "True") == "True"


def get_skill_categories() -> str:
    return getEnv("AI_ENRICHSKILL_CATEGORIES", required=True)


def get_enrich_limit() -> int:
    return int(getEnv("AI_ENRICHSKILL_ENRICH_LIMIT", "10"))


def get_skill_system_prompt() -> str:
    categories = get_skill_categories()
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
