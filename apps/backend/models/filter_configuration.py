from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class FilterConfigurationCreate(BaseModel):
    name: str
    filters: dict
    watched: bool = False
    statistics: bool = True
    pinned: bool = False
    ordering: int = 0

class FilterConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[dict] = None
    watched: Optional[bool] = None
    statistics: Optional[bool] = None
    pinned: Optional[bool] = None
    ordering: Optional[int] = None

class FilterConfiguration(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    filters: dict
    watched: bool
    statistics: bool
    pinned: bool
    ordering: int
    created: datetime
    modified: Optional[datetime] = None
