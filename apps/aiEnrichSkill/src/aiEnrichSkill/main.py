#!/usr/bin/env python
import sys
import time
import warnings
from importlib.metadata import version as _v

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.observability import configure_logging, get_logger
from commonlib.terminalColor import cyan
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.terminalUtil import consoleTimer
from .config import get_enabled
from .services.enrichment_service import enrich_skills

configure_logging("aiEnrichSkill")

logger = get_logger("aiEnrichSkill.main")


def run():
    logger.info("startup", version=_v('aiEnrichSkill'))
    print(cyan(f"AI Skill Enrich v{_v('aiEnrichSkill')}"))

    if not get_enabled():
        logger.info("disabled")
        return

    while True:
        with MysqlUtil() as mysql:
            count = enrich_skills(mysql)
            if count > 0:
                continue
        consoleTimer(cyan('All skills enriched. '), '10s', end='\r')
