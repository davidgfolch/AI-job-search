import json
import os
import structlog
from commonlib.environmentUtil import getEnv, getEnvBool

LOG_DIR = getEnv("AI_ENRICH_LOG_DIR", "data/logs")
LOG_FILE_MAX_BYTES = int(getEnv("AI_ENRICH_LOG_FILE_MAX_BYTES", str(10 * 1024 * 1024)))
LOG_FILE_BACKUP_COUNT = int(getEnv("AI_ENRICH_LOG_FILE_BACKUP_COUNT", "5"))

_configured = False


def _rotate_if_needed(filepath: str):
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > LOG_FILE_MAX_BYTES:
            for i in range(LOG_FILE_BACKUP_COUNT - 1, 0, -1):
                src = f"{filepath}.{i}"
                dst = f"{filepath}.{i + 1}"
                if os.path.exists(src):
                    os.replace(src, dst)
            if os.path.exists(filepath):
                os.replace(filepath, f"{filepath}.1")
    except OSError:
        pass


def configure_logging(app_name: str = "app"):
    global _configured
    if _configured:
        return
    _configured = True

    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{app_name}.jsonl")

    def _jsonl_writer(logger, method_name, event_dict):
        event_dict["logger"] = app_name
        _rotate_if_needed(log_file)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict, default=str, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return event_dict

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _jsonl_writer,
            structlog.dev.ConsoleRenderer()
            if getEnvBool("AI_ENRICH_LOG_COLOR", True)
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            int(getEnv("AI_ENRICH_LOG_LEVEL", "20"))
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    configure_logging()
    return structlog.get_logger(name)
