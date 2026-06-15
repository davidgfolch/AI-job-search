#!/usr/bin/env python
import sys
import warnings
from importlib.metadata import version as _v

from commonlib.environmentUtil import getEnvBool
from commonlib.terminalColor import cyan
from commonlib.observability import get_logger
from .dataExtractor import DataExtractor
from .crew import AiJobSearchFlow
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
        AiJobSearchFlow().kickoff()
    if get_skill_enabled():
        skillEnricher()
    logger.info("shutdown")


def train():
    try:
        n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        filename = sys.argv[2] if len(sys.argv) > 2 else "default_training.txt"
        DataExtractor().crew().train(
            n_iterations=n_iterations, filename=filename, inputs={}
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    try:
        task_id = sys.argv[1] if len(sys.argv) > 1 else "default_task"
        DataExtractor().crew().replay(task_id=task_id)
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test_crew():
    try:
        n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        model_name = sys.argv[2] if len(sys.argv) > 2 else "gpt-3.5-turbo"
    except (ValueError, IndexError):
        n_iterations = 1
        model_name = "gpt-3.5-turbo"
    try:
        DataExtractor().crew().test(
            n_iterations=n_iterations, openai_model_name=model_name, inputs={}
        )
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")
