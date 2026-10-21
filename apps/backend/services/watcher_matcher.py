import json
import threading
import time
from typing import Optional, Any, List, Set, Tuple
from commonlib.observability import get_logger
from repositories.watcher_repository import WatcherRepository
from repositories.watcher_match_repository import WatcherMatchRepository
from repositories.queries.view_generator import _get_where

logger = get_logger("backend.services.watcher_matcher")

POLL_INTERVAL_SECONDS = 8
CLEANUP_INTERVAL_SECONDS = 60 * 60


class WatcherMatcher:
    """Background matcher that enqueues job IDs for watcher_match evaluation."""

    _instance: Optional["WatcherMatcher"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # `__new__` caches the singleton, but Python still calls `__init__` on every
        # `WatcherMatcher()` access. Re-running it would reset `_running`, wipe
        # `_pending_ids` and replace the lock/thread, killing the background matcher
        # as soon as any request resolves the singleton. Initialize exactly once.
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.repo = WatcherRepository()
        self.match_repo = WatcherMatchRepository()
        self._pending_ids: Set[int] = set()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    @classmethod
    def reset_for_testing(cls) -> None:
        cls._instance = None

    def add_pending_ids(self, job_ids: List[int]) -> None:
        """Add job IDs to the pending matching set (called after write commits)."""
        if not job_ids:
            return
        with self._lock:
            self._pending_ids.update(job_ids)

    def start_background_matcher(self) -> None:
        """Start the background thread that matches pending jobs against filters."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._match_loop, daemon=True, name="watcher-matcher"
        )
        self._thread.start()
        logger.info(
            "watcher.background_matcher_started", interval=POLL_INTERVAL_SECONDS
        )

    def stop_background_matcher(self) -> None:
        """Signal the background thread to stop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def _match_loop(self) -> None:
        last_cleanup = time.time()
        while self._running:
            try:
                self._process_pending()
            except Exception as e:
                logger.exception("watcher.match_loop_error", error=str(e))
            now = time.time()
            if now - last_cleanup >= CLEANUP_INTERVAL_SECONDS:
                try:
                    deleted = self.match_repo.cleanup_old_rows(older_than_days=1)
                    logger.info("watcher.cleanup", deleted_rows=deleted)
                except Exception as e:
                    logger.exception("watcher.cleanup_error", error=str(e))
                last_cleanup = now
            time.sleep(POLL_INTERVAL_SECONDS)

    def _process_pending(self) -> None:
        with self._lock:
            pending = set(self._pending_ids)
            self._pending_ids.clear()
        # Safety net: also pick up recently-enriched jobs whose notification may
        # not have reached this matcher instance (e.g. across uvicorn workers).
        pending |= set(self.repo.get_recently_enriched_ids())
        if not pending:
            return

        logger.info("watcher.process_pending", count=len(pending), pending_ids=sorted(pending))
        watched_configs = self.repo.get_watched_configs()
        if not watched_configs:
            logger.info("watcher.process_pending_no_configs", count=len(pending))
            return

        pending_list = sorted(pending)
        existing_ids = self.repo.get_existing_job_ids(pending_list)
        deleted_ids = set(pending_list) - existing_ids

        logger.info(
            "watcher.process_pending_loaded",
            pending=len(pending),
            existing=len(existing_ids),
            deleted=len(deleted_ids),
            watched_configs=len(watched_configs),
        )

        self._handle_deleted_jobs(deleted_ids)
        matched_total = self._match_existing_jobs(existing_ids, watched_configs)

        logger.info(
            "watcher.process_pending_done",
            existing=len(existing_ids),
            deleted=len(deleted_ids),
            matched=matched_total,
        )

    def _handle_deleted_jobs(self, deleted_ids: Set[int]) -> None:
        """Insert tombstones for deleted jobs that had active matches."""
        if not deleted_ids:
            return
        deleted_sorted = sorted(deleted_ids)
        active_matches = self.repo.get_active_matches_for_jobs(deleted_sorted)
        self.match_repo.delete_active_matches_for_jobs(deleted_sorted)
        for cfg_id, job_id in active_matches:
            self.match_repo.insert_tombstone(cfg_id, job_id)

    def _match_existing_jobs(
        self, existing_ids: Set[int], watched_configs: List[Tuple[int, str]]
    ) -> int:
        """Match existing pending jobs against each watched filter config.

        Returns the total number of matches inserted.
        """
        if not existing_ids:
            return 0
        existing_sorted = sorted(existing_ids)
        matched_total = 0
        for cfg_id, filters_json in watched_configs:
            filters = self._parse_filters(filters_json)
            where_part = _get_where(filters) or "1=1"
            matched_ids = self.repo.match_jobs_against_config(
                cfg_id, where_part, existing_sorted
            )
            logger.info(
                "watcher.match_config",
                config_id=cfg_id,
                filters=filters,
                where=where_part,
                matched=len(matched_ids),
                matched_ids=matched_ids,
            )
            for job_id in matched_ids:
                self.match_repo.insert_match(cfg_id, job_id)
                matched_total += 1
        return matched_total

    @staticmethod
    def _parse_filters(filters_json: Any) -> dict:
        """Parse filter JSON into a dict, returning {} on parse failure."""
        if isinstance(filters_json, str):
            try:
                return json.loads(filters_json)
            except (json.JSONDecodeError, TypeError):
                return {}
        return filters_json or {}


def get_watcher_matcher() -> WatcherMatcher:
    """Return the module-level WatcherMatcher singleton."""
    return WatcherMatcher()
