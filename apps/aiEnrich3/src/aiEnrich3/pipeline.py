import os
import warnings
import transformers

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", module="huggingface_hub.*")

transformers.logging.set_verbosity_error()

from typing import Optional
import time
from gliner import GLiNER
from .services.extractors.salary_extractor import SalaryExtractor
from .services.extractors.skills_extractor import SkillsExtractor
from .services.extractors.modality_extractor import ModalityExtractor
from commonlib.observability import get_logger

logger = get_logger("aiEnrich3.pipeline")


class ExtractionPipeline:
    def __init__(self):
        load_start = time.time()
        shared_gliner = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        self.salary_extractor = SalaryExtractor(model=shared_gliner)
        self.skills_extractor = SkillsExtractor(model=shared_gliner)
        self.modality_extractor = ModalityExtractor()
        load_duration = time.time() - load_start
        logger.info("pipeline.loaded", duration=load_duration)

    def process_job(self, text: str) -> dict:
        if not text:
            return {
                "salary": None,
                "required_skills": [],
                "optional_skills": [],
                "modality": None
            }

        start = time.time()

        salary = self.salary_extractor.extract(text)
        required_skills, optional_skills = self.skills_extractor.extract(text)
        modality = self.modality_extractor.extract(text)

        duration = time.time() - start
        logger.debug("pipeline.job_processed", duration=duration)

        return {
            "salary": salary,
            "required_skills": required_skills,
            "optional_skills": optional_skills,
            "modality": modality.value if modality else None
        }
