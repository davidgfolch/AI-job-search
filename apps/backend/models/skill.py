from typing import Optional, List
from pydantic import BaseModel

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    learning_path: Optional[List[str]] = None
    disabled: Optional[bool] = False

class Skill(SkillBase):
    pass

class SkillCreate(SkillBase):
    pass

class SkillUpdate(SkillBase):
    description: Optional[str] = None
    learning_path: Optional[List[str]] = None
    disabled: Optional[bool] = None
