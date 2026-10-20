from typing import Optional, Dict, Any, List
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
        filter_config_service: Optional[Any] = None,
    ) -> Dict[int, Dict[str, int]]:
        """Return {config_id: {"total": N, "new_items": M}} using watcher_match.

        new_items = active matches created after cutoff (per config).
        total = all active matches (ignores cutoff for total).
        """
        cutoff_map = cutoff_map or {}
        results = {cid: {"total": 0, "new_items": 0} for cid in config_ids}
        try:
            active_counts = self.repo.get_match_counts(config_ids)
            for cid, c in active_counts.items():
                results[cid]["total"] = c["active"]
            if cutoff_map:
                latest_cutoff = min(cutoff_map.values())
                recent = self.repo.get_recent_counts(config_ids, latest_cutoff)
                for cid in config_ids:
                    if cid in recent:
                        results[cid]["new_items"] = recent[cid]["new"]
        except Exception as e:
            logger.exception(
                "watcher.stats_failed", error=str(e), config_count=len(config_ids)
            )
        return results


def get_watcher_service() -> WatcherService:
    """Return the module-level WatcherService singleton."""
    return WatcherService()
