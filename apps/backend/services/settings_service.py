from commonlib.environmentUtil import getEnvAll, setEnv
from commonlib.observability import get_logger
from repositories.scrapper_state_repository import ScrapperStateRepository

logger = get_logger("backend.services.settings_service")

_repo = ScrapperStateRepository()

def get_env_settings() -> dict[str, str]:
    return getEnvAll()

def update_env_setting(key: str, value: str) -> dict[str, str]:
    setEnv(key, value)
    logger.info("settings.updated", key=key, count=1)
    return getEnvAll()

def update_env_settings_bulk(updates: dict[str, str]) -> dict[str, str]:
    from commonlib.environmentUtil import setEnvBulk
    setEnvBulk(updates)
    logger.info("settings.updated", count=len(updates))
    return getEnvAll()

def get_scrapper_state() -> dict:
    try:
        return _repo.get_all()
    except Exception as e:
        logger.exception("scrapper_state.read_failed", error=str(e))
        return {}

def update_scrapper_state(state: dict) -> dict:
    try:
        return _repo.replace_all(state)
    except Exception as e:
        logger.exception("scrapper_state.write_failed", error=str(e))
        return state
