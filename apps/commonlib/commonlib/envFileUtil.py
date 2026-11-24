import os
from dotenv import dotenv_values

from commonlib.environmentUtil import ENV_PATH, ENV_SECRETS_PATH


def getEnvFile(key: str, default: str = None) -> str:
    """Read a key from the .env files, bypassing the captured process environment.

    Compose injects `.env` into containers at startup, so `getEnv` keeps returning the
    startup value after Settings edits the file. Live switches read the file directly;
    the process environment is only a fallback for keys absent from both files.
    """
    main_values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    secret_values = dotenv_values(ENV_SECRETS_PATH) if ENV_SECRETS_PATH.exists() else {}
    values = {**main_values, **secret_values}
    value = values.get(key)
    return value if value is not None else os.environ.get(key, default)
