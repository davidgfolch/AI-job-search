import os
import structlog
from commonlib.environmentUtil import getEnv, getEnvBool

LOG_DIR = getEnv("AI_ENRICH_LOG_DIR", "data/logs")
LOG_FILE = os.path.join(LOG_DIR, "aienrich.jsonl")

_configured = False

def configure_logging():
    global _configured
    if _configured:
        return
    _configured = True

    os.makedirs(LOG_DIR, exist_ok=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if getEnvBool("AI_ENRICH_LOG_COLOR", True)
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            int(getEnv("AI_ENRICH_LOG_LEVEL", "20"))  # 20=INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    configure_logging()
    return structlog.get_logger(name)
