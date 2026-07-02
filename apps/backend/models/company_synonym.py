from typing import Optional, List
from pydantic import BaseModel

class SynonymGroup(BaseModel):
    group_id: int
    names: List[str]

class SynonymGroupCreate(BaseModel):
    names: List[str]

class SynonymAddRequest(BaseModel):
    name: str
