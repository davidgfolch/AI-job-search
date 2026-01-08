import os
from dotenv import load_dotenv
from .terminalColor import yellow

def getEnvModified() -> float | None:
    x = os.stat('../../.env').st_ctime if os.stat('../../.env') else None
    return x

# Initialize module-level state
load_dotenv()
envLastModified = getEnvModified()

def checkEnvReload():
    global envLastModified
    modified = envLastModified == getEnvModified()
    if modified:
        return
    print(yellow('Reloading .env'))
    load_dotenv(override=True)
    envLastModified = getEnvModified()

def getEnv(key: str, default: str = None) -> str:
    checkEnvReload()
    v = os.environ.get(key, default)
    return v

def getEnvMultiline(key: str, default: str = None) -> str:
    idx = 1
    value = ''
    while True:
        partialValue = getEnv(f'{key}_{idx}')
        if partialValue is None:
            break
        value += partialValue
        idx += 1
    return value

def getEnvBool(key: str, default: bool = False) -> bool:
    v = getEnv(key, str(default) if default else None)
    if v is None:
        return default
    return v.lower() == "true"

def getEnvByPrefix(prefix: str) -> dict[str, str]:
    checkEnvReload()
    result = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            result[key[len(prefix):]] = value
    return result
