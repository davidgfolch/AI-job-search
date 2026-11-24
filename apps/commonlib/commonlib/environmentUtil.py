import os
import re
import threading
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

from commonlib.envWriteUtil import set_keys

env_lock = threading.Lock()

ENV_LOGGER_NAME = "commonlib.environmentUtil"


def _logger():
    """Return the shared structured logger.

    This module is imported by `commonlib.observability` (directly and through
    `console_render`) while that module is still initializing, so `get_logger` cannot be
    imported at module level without a circular import. Importing it here runs only when
    a record is actually emitted, after observability has finished loading.
    """
    from commonlib.observability import get_logger
    return get_logger(ENV_LOGGER_NAME)

# Resolve .env paths relative to this file: 
# apps/commonlib/commonlib/environmentUtil.py -> ../../../.env (Root)
ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / '.env'
ENV_SECRETS_PATH = Path(__file__).resolve().parent.parent.parent.parent / '.env.secrets'
ENV_SECRETS_EXAMPLE_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'scripts' / '.env.secrets.example'

_SECRET_KEY_LINE = re.compile(r"^\s*#?\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")

def _secret_env_keys() -> set[str]:
    if not ENV_SECRETS_EXAMPLE_PATH.exists():
        return set()
    return {m.group(1) for line in ENV_SECRETS_EXAMPLE_PATH.read_text(encoding='utf-8').splitlines() if (m := _SECRET_KEY_LINE.match(line))}

def _get_mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0

def getEnvModified() -> float | None:
    mtime = max(_get_mtime(ENV_PATH), _get_mtime(ENV_SECRETS_PATH))
    return mtime if mtime > 0 else None

_envLoadedLogged = False
_envReloading = False

def _logEnvLoaded():
    global _envLoadedLogged
    if _envLoadedLogged or _envReloading:
        return
    _envLoadedLogged = True
    logger = _logger()
    logger.info('env.loaded', paths=[str(ENV_PATH), str(ENV_SECRETS_PATH)])

# Real process environment (Docker Compose `environment:`, shell exports) captured
# before the first dotenv load. It outranks the dotenv files, so it is re-asserted
# after every override reload: hot-reload must apply edited .env values without
# letting a stray .env key clobber an injected one (e.g. COMMONLIB_DB_HOST).
_processEnvSnapshot = dict(os.environ)

def _restoreProcessEnv():
    os.environ.update(_processEnvSnapshot)

# Initialize module-level state. Same order and precedence as the reload path:
# `.env` then `.env.secrets` overlay, then the process environment is re-asserted.
load_dotenv(dotenv_path=ENV_PATH, override=True)
load_dotenv(dotenv_path=ENV_SECRETS_PATH, override=True)
_restoreProcessEnv()
envLastModified = getEnvModified()

def checkEnvReload():
    global envLastModified, _envReloading
    _logEnvLoaded()
    modified = envLastModified == getEnvModified()
    if modified or _envReloading:
        return
    _envReloading = True
    try:
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        load_dotenv(dotenv_path=ENV_SECRETS_PATH, override=True)
        _restoreProcessEnv()
        envLastModified = getEnvModified()
        _logger().info('env.reloaded', paths=[str(ENV_PATH), str(ENV_SECRETS_PATH)])
    finally:
        _envReloading = False

def getEnv(key: str, default: str = None, required: bool = False) -> str:
    checkEnvReload()
    v = os.environ.get(key, default)
    if required and v is None:
        raise ValueError(f"Required environment variable '{key}' not found in .venv")
    return v

def getEnvMultiline(key: str, required: bool = False) -> str:
    idx = 1
    value = ''
    while True:
        partialValue = getEnv(f'{key}_{idx}', required=required)
        if partialValue is None:
            break
        value += partialValue
        idx += 1
    return value

def getEnvBool(key: str, default: bool = False, required: bool = False) -> bool:
    v = getEnv(key, str(default) if default else None, required=required)
    if v is None:
        return default
    return v.lower() == "true"

def getEnvByPrefix(prefix: str, required: bool = False) -> dict[str, str]:
    checkEnvReload()
    result = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            result[key[len(prefix):]] = value
    if required and not result:
        raise ValueError(f"Required environment variables with prefix '{prefix}' not found in .venv")
    return result

def getEnvAll() -> dict[str, str]:
    """Returns all env vars from .env.secrets.example, overlayed with actual values from .env and .env.secrets"""
    example_secrets = dotenv_values(ENV_SECRETS_EXAMPLE_PATH) if ENV_SECRETS_EXAMPLE_PATH.exists() else {}
    actual_main = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    actual_secrets = dotenv_values(ENV_SECRETS_PATH) if ENV_SECRETS_PATH.exists() else {}
    example_values = example_secrets
    actual_values = {**actual_main, **actual_secrets}
    if not example_values:
        return actual_values
    result = {}
    for k, v in example_values.items():
        result[k] = actual_values.get(k, v) if actual_values.get(k) is not None else v
    for k, v in actual_values.items():
        if k not in result:
            result[k] = v
    return result

def _write_keys(path: Path, updates: dict[str, str]):
    if not updates:
        return
    if path.exists():
        set_keys(path, updates)
    else:
        with open(path, 'w', encoding='utf-8') as f:
            for key, value in updates.items():
                f.write(f"{key}={value}\n")


def _apply_env_updates(updates: dict[str, str]):
    global envLastModified
    secret_keys = _secret_env_keys()
    with env_lock:
        _write_keys(ENV_PATH, {k: v for k, v in updates.items() if k not in secret_keys})
        _write_keys(ENV_SECRETS_PATH, {k: v for k, v in updates.items() if k in secret_keys})
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    load_dotenv(dotenv_path=ENV_SECRETS_PATH, override=True)
    _restoreProcessEnv()
    envLastModified = getEnvModified()

def setEnv(key: str, value: str):
    """Updates a single key in .env or .env.secrets and reloads the environment"""
    _apply_env_updates({key: value})

def setEnvBulk(updates: dict[str, str]):
    """Updates multiple keys in .env or .env.secrets and reloads the environment"""
    _apply_env_updates(updates)

