from pydantic import BaseModel
from typing import Dict, Any

class SettingsEnvUpdateDto(BaseModel):
    key: str
    value: str

class SettingsEnvBulkUpdateDto(BaseModel):
    updates: Dict[str, str]

class ScrapperStateUpdateDto(BaseModel):
    state: Dict[str, Any]
