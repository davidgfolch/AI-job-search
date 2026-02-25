from fastapi import APIRouter
from services import settings_service as service
from models.settings import SettingsEnvUpdateDto, ScrapperStateUpdateDto

router = APIRouter()

@router.get("/env")
def get_env_settings():
    return service.get_env_settings()

@router.post("/env")
def update_env_setting(update: SettingsEnvUpdateDto):
    return service.update_env_setting(update.key, update.value)

from models.settings import SettingsEnvBulkUpdateDto
@router.post("/env-bulk")
def update_env_settings_bulk(update: SettingsEnvBulkUpdateDto):
    return service.update_env_settings_bulk(update.updates)

@router.get("/scrapper-state")
def get_scrapper_state():
    return service.get_scrapper_state()

@router.post("/scrapper-state")
def update_scrapper_state(update: ScrapperStateUpdateDto):
    return service.update_scrapper_state(update.state)
