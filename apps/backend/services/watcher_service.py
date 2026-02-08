from typing import Optional, Dict, Any, List
from repositories.watcher_repository import WatcherRepository
from datetime import datetime
from commonlib.terminalColor import red

class WatcherService:
    
    def __init__(self):
        self.repo = WatcherRepository()
    
    def _parse_cutoff(self, cutoff_str: str):
        from datetime import datetime
        try:
            # Handle Z for UTC which might not be supported in older python fromisoformat
            if cutoff_str.endswith('Z'):
                cutoff_str = cutoff_str[:-1] + '+00:00'
            dt = datetime.fromisoformat(cutoff_str)
            # If naive, assume local time and make it aware
            if dt.tzinfo is None:
                dt = dt.astimezone()
            return dt
        except:
            return None

    def get_watcher_stats(self, config_ids: List[int],
                          cutoff_map: Optional[Dict[int, str]] = None,
                          filter_config_service: Optional[Any] = None) -> Dict[int, Dict[str, int]]:
        cutoff_map = cutoff_map or {}
        results = {cid: {"total": 0, "new_items": 0} for cid in config_ids}
        try:
            rows = self.repo.get_watcher_stats_from_view(config_ids)
            for row in rows:
                config_id = row[0]
                job_created = row[1]
                if config_id in results:
                    stats = results[config_id]
                    stats["total"] += 1
                    if cutoff_str := cutoff_map.get(config_id):
                        if self._is_new(cutoff_str, job_created):
                            stats["new_items"] += 1
        except Exception as e:
            print(red(f"Error fetching watcher stats from view: {e}"))
            pass
        return results

    def _is_new(self, cutoff_str: str, job_created: Any) -> bool:
        try:
            cutoff_dt = self._parse_cutoff(cutoff_str)
            if not cutoff_dt:
                return False
            if isinstance(job_created, str):
                job_created = datetime.fromisoformat(job_created.replace('Z', '+00:00'))
            if not isinstance(job_created, datetime):
                return False
            job_created_aware = job_created if job_created.tzinfo else job_created.astimezone()
            return job_created_aware > cutoff_dt
        except Exception as e:
            print(red(f"Error comparing dates for {cutoff_str}: {e}"))
            return False


