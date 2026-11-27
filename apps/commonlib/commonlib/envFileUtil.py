import os
from dotenv import dotenv_values

from commonlib.environmentUtil import ENV_LOCAL_PATH, ENV_PATH, ENV_SECRETS_PATH


def getEnvFile(key: str, default: str = None) -> str:
    """Read a key from the .env files, bypassing the captured process environment.

    Compose injects `.env` into containers at startup, so `getEnv` keeps returning the
    startup value after Settings edits the file. Live switches read the file directly;
    the process environment is only a fallback for keys absent from all env files.
    Precedence: .env < .env.local < .env.secrets < process env fallback.
    """
    main_values = dotenv_values(ENV_PATH) if ENV_PATH.is_file() else {}
    local_values = dotenv_values(ENV_LOCAL_PATH) if ENV_LOCAL_PATH.is_file() else {}
    secret_values = dotenv_values(ENV_SECRETS_PATH) if ENV_SECRETS_PATH.is_file() else {}
    values = {**main_values, **local_values, **secret_values}
    value = values.get(key)
    return value if value is not None else os.environ.get(key, default)
