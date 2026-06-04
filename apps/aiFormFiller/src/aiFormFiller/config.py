from commonlib.environmentUtil import getEnv, getEnvBool


def get_provider() -> str:
    return getEnv("AI_FORM_PROVIDER", "local")


def get_port() -> int:
    return int(getEnv("AI_FORM_PORT", "8080"))


def get_hf_model() -> str:
    return getEnv("AI_FORM_HF_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")


def get_openai_api_key() -> str | None:
    return getEnv("OPENAI_API_KEY")


def get_openai_model() -> str:
    return getEnv("OPENAI_MODEL", "gpt-4o-mini")


def get_openrouter_api_key() -> str | None:
    return getEnv("OPENROUTER_API_KEY")


def get_openrouter_model() -> str:
    return getEnv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def get_cv_path() -> str:
    return getEnv("AI_FORM_CV_PATH", "cv/cv.txt")


def get_looking_for_path() -> str:
    return getEnv("AI_FORM_LOOKING_FOR_PATH", "cv/looking-for.txt")


def get_timeout() -> float:
    return float(getEnv("AI_FORM_TIMEOUT", "30"))


def get_temperature() -> float:
    return float(getEnv("AI_FORM_TEMPERATURE", "0.1"))


def get_max_tokens() -> int:
    return int(getEnv("AI_FORM_MAX_TOKENS", "512"))
