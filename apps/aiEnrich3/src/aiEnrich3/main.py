import sys
import io
import time
from importlib.metadata import version as _v
from typing import Optional

from aiEnrich3.dataExtractor import dataExtractor
from aiEnrich3.pipeline import ExtractionPipeline
from aiEnrich3.config import get_job_enabled, get_skill_enabled
from commonlib.observability import get_logger
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.terminalColor import cyan

logger = get_logger("aiEnrich3.main")
collector = MetricsCollector()


def run():
    logger.info("startup", version=_v('aiEnrich3'))
    print(cyan(f"AI Enrich3 v{_v('aiEnrich3')}"))
    pipeline: Optional[ExtractionPipeline] = None
    while True:
        if get_job_enabled():
            processed, pipeline = dataExtractor(pipeline)
            if processed > 0:
                collector.persist()
                continue
        if get_skill_enabled():
            pass

        print(cyan("All jobs enriched. I'll retry in 10s ..."), flush=True)
        time.sleep(10)


if __name__ == "__main__":
    if sys.stdout and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    run()
