from typing import List
from commonlib.observability import get_logger
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection

logger = get_logger("backend.repositories.watcher_match_repository")


class WatcherMatchRepository:
    """Write operations for watcher_match table (inserts, deletes, cleanup)."""

    def get_db(self):
        return MysqlUtil(getConnection())

    def insert_match(self, config_id: int, job_id: int) -> None:
        """Insert a single active match (deleted=0)."""
        with self.get_db() as db:
            db.executeAndCommit(
                "INSERT IGNORE INTO watcher_match (config_id, job_id, deleted) VALUES (%s, %s, 0)",
                (config_id, job_id),
            )

    def insert_tombstone(self, config_id: int, job_id: int) -> None:
        """Insert a single tombstone (deleted=1)."""
        with self.get_db() as db:
            db.executeAndCommit(
                "INSERT IGNORE INTO watcher_match (config_id, job_id, deleted) VALUES (%s, %s, 1)",
                (config_id, job_id),
            )

    def delete_active_matches_for_jobs(self, job_ids: List[int]) -> None:
        """Delete all active (deleted=0) watcher_match rows for given job IDs."""
        if not job_ids:
            return
        with self.get_db() as db:
            ids_str = ", ".join(["%s"] * len(job_ids))
            db.executeAndCommit(
                f"DELETE FROM watcher_match WHERE job_id IN ({ids_str}) AND deleted = 0",
                tuple(job_ids),
            )

    def cleanup_old_rows(self, older_than_days: int = 1) -> int:
        """Delete watcher_match rows older than N days (default: yesterday)."""
        with self.get_db() as db:
            result = db.executeAndCommit(
                "DELETE FROM watcher_match WHERE created_at < DATE_SUB(CURDATE(), INTERVAL %s DAY)",
                (older_than_days,),
            )
        return result
