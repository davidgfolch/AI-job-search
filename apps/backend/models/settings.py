from pydantic import BaseModel
from typing import Dict, Any

class SettingsEnvUpdateDto(BaseModel):
    key: str
    value: str

class SettingsEnvBulkUpdateDto(BaseModel):
    updates: Dict[str, str]

class ScrapperStateUpdateDto(BaseModel):
    state: Dict[str, Any]

class ProviderModel(BaseModel):
    id: str
    label: str
    free: bool

class ProviderModelsResponse(BaseModel):
    provider: str
    models: list[ProviderModel]
    source: str
    cached: bool
    fetched_at: float | None = None
