#!/usr/bin/env python
import warnings
from importlib.metadata import version as _v

from commonlib.environmentUtil import getEnvBool
from commonlib.terminalColor import cyan
from commonlib.observability import configure_logging, get_logger
from .pipeline import run_pipeline

configure_logging("aiEnrich")
from .skillEnricher import skillEnricher

logger = get_logger("aiEnrich.main")


def get_job_enabled() -> bool:
    return getEnvBool("AI_ENRICH_JOB", True)


def get_skill_enabled() -> bool:
    return getEnvBool("AI_ENRICH_SKILL", True)


warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    logger.info("startup", version=_v('aiEnrich'))
    print(cyan(f"AI Enrich v{_v('aiEnrich')}"))
    if get_job_enabled():
        run_pipeline()
    if get_skill_enabled():
        skillEnricher()
    logger.info("shutdown")
