from typing import Optional, List
from pydantic import BaseModel

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    learning_path: Optional[List[str]] = None
    disabled: Optional[bool] = False
    ai_enriched: Optional[bool] = False
    category: Optional[str] = None

class Skill(SkillBase):
    pass

class SkillCreate(SkillBase):
    pass

class SkillUpdate(SkillBase):
    name: Optional[str] = None
    disabled: Optional[bool] = None
    ai_enriched: Optional[bool] = None
