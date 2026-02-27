import os


def getEnvBool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")


def get_job_enabled() -> bool:
    return getEnvBool("AI_ENRICH3_JOB", True)


def get_skill_enabled() -> bool:
    return getEnvBool("AI_ENRICH3_SKILL", False)


def get_input_max_len() -> int:
    return int(os.environ.get("AI_ENRICH3_INPUT_MAX_LEN", 10000))


def get_batch_size() -> int:
    return int(os.environ.get("AI_ENRICH3_MAX_CONCURRENCY", 4))
