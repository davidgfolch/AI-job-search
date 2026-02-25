from commonlib.environmentUtil import getEnvAll, setEnv
import json
from pathlib import Path

# Path to scrapper_state.json relative to this file
SCRAPPER_STATE_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'apps' / 'scrapper' / 'scrapper_state.json'

def get_env_settings() -> dict[str, str]:
    return getEnvAll()

def update_env_setting(key: str, value: str) -> dict[str, str]:
    setEnv(key, value)
    return getEnvAll()

def update_env_settings_bulk(updates: dict[str, str]) -> dict[str, str]:
    from commonlib.environmentUtil import setEnvBulk
    setEnvBulk(updates)
    return getEnvAll()

def get_scrapper_state() -> dict:
    if not SCRAPPER_STATE_PATH.exists():
        return {}
    try:
        with open(SCRAPPER_STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print("Error reading scrapper state:", e)
        return {}

def update_scrapper_state(state: dict) -> dict:
    # Ensure directory exists
    SCRAPPER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCRAPPER_STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    return state
