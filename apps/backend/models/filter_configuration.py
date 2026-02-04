from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class FilterConfigurationCreate(BaseModel):
    name: str
    filters: dict
    notify: bool = False
    statistics: bool = True
    pinned: bool = False

class FilterConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[dict] = None
    notify: Optional[bool] = None
    statistics: Optional[bool] = None
    pinned: Optional[bool] = None

class FilterConfiguration(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    filters: dict
    notify: bool
    statistics: bool
    pinned: bool
    created: datetime
    modified: Optional[datetime] = None
