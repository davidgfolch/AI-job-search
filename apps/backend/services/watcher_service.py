from typing import Optional, Dict, List
from commonlib.observability import get_logger
from repositories.watcher_repository import WatcherRepository

logger = get_logger("backend.services.watcher_service")


class WatcherService:
    """Service for watcher stats reads."""

    _instance: Optional["WatcherService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.repo = WatcherRepository()

    @classmethod
    def reset_for_testing(cls) -> None:
        cls._instance = None

    def get_watcher_stats(
        self,
        config_ids: List[int],
        cutoff_map: Optional[Dict[int, str]] = None,
    ) -> Dict[int, Dict[str, int]]:
        """Return {config_id: {"total": N, "new_items": M, "removed_items": R}} using watcher_match.

        new_items = active matches created after the cutoff of that configuration.
        removed_items = tombstones created after the same cutoff.
        total = all active matches (ignores cutoff for total).

        Each configuration is counted with its own cutoff: a configuration the user
        reloaded recently must not be counted with the oldest cutoff of the batch.
        """
        cutoff_map = cutoff_map or {}
        results = {
            cid: {"total": 0, "new_items": 0, "removed_items": 0} for cid in config_ids
        }
        try:
            active_counts = self.repo.get_match_counts(config_ids)
            for cid, c in active_counts.items():
                results[cid]["total"] = c["active"]
            if cutoff_map:
                recent = self.repo.get_recent_counts(config_ids, cutoff_map)
                for cid in config_ids:
                    if cid in recent:
                        results[cid]["new_items"] = recent[cid].get("new", 0)
                        results[cid]["removed_items"] = recent[cid].get("removed", 0)
        except Exception as e:
            logger.exception(
                "watcher.stats_failed", error=str(e), config_count=len(config_ids)
            )
        return results


def get_watcher_service() -> WatcherService:
    """Return the module-level WatcherService singleton."""
    return WatcherService()
