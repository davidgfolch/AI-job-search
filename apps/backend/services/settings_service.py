from commonlib.environmentUtil import getEnvAll, setEnv
from repositories.scrapper_state_repository import ScrapperStateRepository

_repo = ScrapperStateRepository()

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
    try:
        return _repo.get_all()
    except Exception as e:
        print("Error reading scrapper state:", e)
        return {}

def update_scrapper_state(state: dict) -> dict:
    try:
        return _repo.replace_all(state)
    except Exception as e:
        print("Error updating scrapper state:", e)
        return state
