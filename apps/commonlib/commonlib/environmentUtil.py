import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values, set_key
from .terminalColor import yellow

# Resolve .env path relative to this file: 
# apps/commonlib/commonlib/environmentUtil.py -> ../../../.env (Root)
ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / '.env'
ENV_EXAMPLE_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'scripts' / '.env.example'

def getEnvModified() -> float | None:
    if not ENV_PATH.exists():
        return None
    return ENV_PATH.stat().st_ctime

# Initialize module-level state
load_dotenv(dotenv_path=ENV_PATH)
envLastModified = getEnvModified()

def checkEnvReload():
    global envLastModified
    modified = envLastModified == getEnvModified()
    if modified:
        return
    print(yellow('Reloading .env'))
    load_dotenv(override=True)
    envLastModified = getEnvModified()

def getEnv(key: str, default: str = None, required: bool = False) -> str:
    checkEnvReload()
    v = os.environ.get(key, default)
    if required and v is None:
        raise ValueError(f"Required environment variable '{key}' not found in .venv")
    return v

def getEnvMultiline(key: str, default: str = None, required: bool = False) -> str:
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
    """Returns a dictionary containing all keys from .env.example with their current values from .env (or default from .env.example)"""
    example_values = dotenv_values(ENV_EXAMPLE_PATH) if ENV_EXAMPLE_PATH.exists() else {}
    actual_values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    
    if not example_values:
        return actual_values

    result = {}
    for k, v in example_values.items():
        result[k] = actual_values.get(k, v) if actual_values.get(k) is not None else v
        
    # Inject variables only in .env (if any)
    for k, v in actual_values.items():
        if k not in result:
            result[k] = v
            
    return result

def setEnv(key: str, value: str):
    """Updates a single key in the .env file and reloads the environment"""
    if ENV_PATH.exists():
        set_key(str(ENV_PATH), key, value)
    else:
        with open(ENV_PATH, 'w', encoding='utf-8') as f:
            f.write(f"{key}={value}\n")
    
    global envLastModified
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    envLastModified = getEnvModified()

def setEnvBulk(updates: dict[str, str]):
    """Updates multiple keys in the .env file and reloads the environment"""
    if ENV_PATH.exists():
        for key, value in updates.items():
            set_key(str(ENV_PATH), key, value)
    else:
        with open(ENV_PATH, 'w', encoding='utf-8') as f:
            for key, value in updates.items():
                f.write(f"{key}={value}\n")
    
    global envLastModified
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    envLastModified = getEnvModified()

