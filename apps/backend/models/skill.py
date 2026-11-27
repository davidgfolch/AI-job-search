from typing import Optional, List
from pydantic import BaseModel, field_validator
from commonlib.skill_learning_path import LEARNING_PATH_SOURCES, SOURCE_UNKNOWN

class LearningPathLink(BaseModel):
    url: str
    source: str = SOURCE_UNKNOWN

    @field_validator("source")
    @classmethod
    def _known_source(cls, value: str) -> str:
        return value if value in LEARNING_PATH_SOURCES else SOURCE_UNKNOWN

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    learning_path: Optional[List[LearningPathLink]] = None
    disabled: Optional[bool] = False
    ai_enriched: Optional[bool] = False
    category: Optional[str] = None

    @field_validator("learning_path", mode="before")
    @classmethod
    def _coerce_legacy_links(cls, value):
        if not isinstance(value, list):
            return value
        return [{"url": item, "source": SOURCE_UNKNOWN} if isinstance(item, str) else item for item in value]

class Skill(SkillBase):
    pass

class SkillCreate(SkillBase):
    pass

class SkillUpdate(SkillBase):
    name: Optional[str] = None
    disabled: Optional[bool] = None
    ai_enriched: Optional[bool] = None
