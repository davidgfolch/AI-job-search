import os
import warnings
import transformers

# Suppress HuggingFace Hub warnings (like unauthenticated requests)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", module="huggingface_hub.*")

# Suppress Transformers load report warnings
transformers.logging.set_verbosity_error()

from typing import Optional
from gliner import GLiNER
from .services.extractors.salary_extractor import SalaryExtractor
from .services.extractors.skills_extractor import SkillsExtractor
from .services.extractors.modality_extractor import ModalityExtractor
class ExtractionPipeline:
    """
    Holds the stateful Machine Learning models so they are loaded exactly once 
    and shared across processing batches.
    """
    def __init__(self):
        # Load the base GLiNER model once and share it to save ~1GB of RAM/VRAM
        shared_gliner = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        
        self.salary_extractor = SalaryExtractor(model=shared_gliner)
        self.skills_extractor = SkillsExtractor(model=shared_gliner)
        
        # Load the independent mDeBERTa zero-shot model
        self.modality_extractor = ModalityExtractor()
        
    def process_job(self, text: str) -> dict:
        """
        Runs the full extraction pipeline efficiently over a single text.
        """
        if not text:
            return {
                "salary": None,
                "required_skills": [],
                "optional_skills": [],
                "modality": None
            }
            
        salary = self.salary_extractor.extract(text)
        required_skills, optional_skills = self.skills_extractor.extract(text)
        modality = self.modality_extractor.extract(text)
        
        return {
            "salary": salary,
            "required_skills": required_skills,
            "optional_skills": optional_skills,
            "modality": modality.value if modality else None
        }
