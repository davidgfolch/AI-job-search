from typing import Optional
from warnings import deprecated
from pydantic import BaseModel


# NOTE: CHECKOUT ddl.sql
@deprecated("It is pining for the fiords")
# autopep8:off
class JobTaskOutputModel(BaseModel):
    salary: Optional[str]
    required_technologies: Optional[str]
    optional_technologies: Optional[str]
    relocation: Optional[str]
    business_sector: Optional[str]
    required_languages: Optional[str]
