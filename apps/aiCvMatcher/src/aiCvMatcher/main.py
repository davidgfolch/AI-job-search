#!/usr/bin/env python
import sys
import warnings
from importlib.metadata import version as _v

# Validated lazy imports
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from commonlib.environmentUtil import getEnvBool
from commonlib.observability import configure_logging, get_logger
from commonlib.ai_helpers import logIdleWait
from commonlib.terminalColor import cyan
from .cvMatcher import FastCVMatcher

logger = get_logger("aiCvMatcher.main")

def run():
    configure_logging("aiCvMatcher")
    logger.info("app.started", version=_v('aiCvMatcher'))
    if getEnvBool('AI_CVMATCHER_ENABLED'):
        cvMatcher = FastCVMatcher.instance()
    else:
        logger.info("app.disabled", flag="AI_CVMATCHER_ENABLED")
        sys.exit(0)

    while True:
        if cvMatcher.process_db_jobs() > 0:
            continue
        logIdleWait(cyan('All CV matches calculated.'), '10s', "jobs.skipped", reason="no_pending_jobs")

if __name__ == "__main__":
    run()
