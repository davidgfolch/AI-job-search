from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class ModalityType(str, Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ON_SITE = "ON_SITE"

@dataclass
class ExtractionResult:
    salary: Optional[str] = None
    required_skills: Optional[List[str]] = None
    optional_skills: Optional[List[str]] = None
    modality: Optional[ModalityType] = None
