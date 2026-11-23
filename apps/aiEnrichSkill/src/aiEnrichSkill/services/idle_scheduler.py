import time

from commonlib.observability import get_logger
from commonlib.ollama_activity import busy_seconds

from ..config import get_learning_path_max_failures, get_learning_path_retry_seconds, get_learning_paths_enabled

logger = get_logger("aiEnrichSkill.idle_scheduler")


class LearningPathScheduler:
    """Decides when the low-priority learning-path backfill may touch the model.

    Model exclusivity is enforced by `commonlib.ollama_activity.request_slot`; this class
    keeps the failure breaker and logs the idle/backfill transitions once each, so the
    worker is visible in the logs without one line per idle cycle. After a cooldown the
    breaker half-opens for one trial, so a temporary failure cannot silence the worker
    until it is restarted.
    """

    def __init__(self, max_failures: int | None = None, retry_seconds: int | None = None):
        self._max_failures = get_learning_path_max_failures() if max_failures is None else max_failures
        self._retry_seconds = get_learning_path_retry_seconds() if retry_seconds is None else retry_seconds
        self._failures = 0
        self._open = False
        self._opened_at: float | None = None
        self._state = None

    def note_deferred(self, reason: str) -> None:
        if self._state == "deferred":
            return
        self._state = "deferred"
        logger.info("skill.learning_path.deferred", reason=reason, model_busy_seconds=_as_int(busy_seconds()))

    def note_started(self) -> None:
        if self._state == "running":
            return
        self._state = "running"
        logger.info("skill.learning_path.started")

    def note_stopped(self) -> None:
        self._state = None

    def note_success(self) -> None:
        self._failures = 0

    def note_failure(self) -> bool:
        self._failures += 1
        if self._failures >= self._max_failures:
            self._open = True
            self._opened_at = time.monotonic()
            logger.warning("skill.learning_path.backoff", failures=self._failures, max_failures=self._max_failures, retry_after_seconds=self._retry_seconds)
        return self._open

    def ready(self) -> bool:
        if self._open and self._opened_at is not None and time.monotonic() - self._opened_at >= self._retry_seconds:
            self._open = False
            self._opened_at = None
            logger.info("skill.learning_path.retry", retry_after_seconds=self._retry_seconds)
        return not self._open

    @property
    def deferred(self) -> bool:
        return self._state == "deferred"


def _as_int(value: float | None) -> int | None:
    return None if value is None else int(value)


def should_run_learning_paths(scheduler: LearningPathScheduler) -> bool:
    return get_learning_paths_enabled() and scheduler.ready()
