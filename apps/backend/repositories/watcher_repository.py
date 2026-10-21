from typing import List, Optional, Dict, Any, Set, Tuple
from commonlib.observability import get_logger
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection

logger = get_logger("backend.repositories.watcher_repository")


class WatcherRepository:
    """Read operations for watcher_match table - stats and config discovery."""

    def get_db(self):
        return MysqlUtil(getConnection())

    def get_match_counts(
        self, config_ids: List[int]
    ) -> Dict[int, Dict[str, int]]:
        """Return {config_id: {"active": N, "deleted": M}} counts."""
        if not config_ids:
            return {}
        counts = {cid: {"active": 0, "deleted": 0} for cid in config_ids}
        with self.get_db() as db:
            ids_str = ", ".join(["%s"] * len(config_ids))
            query = f"""
                SELECT config_id, deleted, COUNT(*) as cnt
                FROM watcher_match
                WHERE config_id IN ({ids_str})
                GROUP BY config_id, deleted
            """
            rows = db.fetchAll(query, tuple(config_ids))
        for row in rows:
            config_id = row[0]
            deleted = bool(row[1])
            cnt = int(row[2])
            if config_id in counts:
                key = "deleted" if deleted else "active"
                counts[config_id][key] = cnt
        return counts

    def get_recent_counts(
        self, config_ids: List[int], cutoff: str
    ) -> Dict[int, Dict[str, int]]:
        """Return {config_id: {"new": N, "removed": M}} for rows created after cutoff."""
        if not config_ids:
            return {}
        counts = {cid: {"new": 0, "removed": 0} for cid in config_ids}
        with self.get_db() as db:
            ids_str = ", ".join(["%s"] * len(config_ids))
            query = f"""
                SELECT config_id, deleted, COUNT(*) as cnt
                FROM watcher_match
                WHERE config_id IN ({ids_str})
                  AND created_at > %s
                GROUP BY config_id, deleted
            """
            params = tuple(config_ids) + (cutoff,)
            rows = db.fetchAll(query, params)
        for row in rows:
            config_id = row[0]
            deleted = bool(row[1])
            cnt = int(row[2])
            if config_id in counts:
                key = "removed" if deleted else "new"
                counts[config_id][key] = cnt
        return counts

    def get_watched_configs(self) -> List[Tuple[int, str]]:
        """Return [(config_id, filters_json)] for all watched configs."""
        with self.get_db() as db:
            rows = db.fetchAll(
                "SELECT id, filters FROM filter_configurations WHERE watched = 1"
            )
        return [(int(r[0]), r[1]) if r[1] else (int(r[0]), "{}") for r in rows]

    def get_existing_job_ids(self, job_ids: List[int]) -> Set[int]:
        """Return the subset of job_ids that still exist in the jobs table."""
        if not job_ids:
            return set()
        with self.get_db() as db:
            ids_str = ", ".join(["%s"] * len(job_ids))
            rows = db.fetchAll(
                f"SELECT id FROM jobs WHERE id IN ({ids_str})",
                tuple(job_ids),
            )
        return {int(r[0]) for r in rows}

    def get_active_matches_for_jobs(
        self, job_ids: List[int]
    ) -> List[Tuple[int, int]]:
        """Return [(config_id, job_id)] for active (deleted=0) matches of given jobs."""
        if not job_ids:
            return []
        with self.get_db() as db:
            ids_str = ", ".join(["%s"] * len(job_ids))
            rows = db.fetchAll(
                f"SELECT config_id, job_id FROM watcher_match WHERE job_id IN ({ids_str}) AND deleted = 0",
                tuple(job_ids),
            )
        return [(int(r[0]), int(r[1])) for r in rows]

    def match_jobs_against_config(
        self, config_id: int, where_part: str, job_ids: List[int]
    ) -> List[int]:
        """Return the subset of job_ids that match the config's filter where clause."""
        if not job_ids:
            return []
        ids_str = ", ".join(["%s"] * len(job_ids))
        query = f"""
            SELECT id FROM jobs
            WHERE {where_part}
              AND id IN ({ids_str})
        """
        with self.get_db() as db:
            rows = db.fetchAll(query, tuple(job_ids))
        return [int(r[0]) for r in rows]

    def get_recently_enriched_ids(self, since_minutes: int = 10) -> List[int]:
        """Return recently-enriched job ids that have no active watcher_match row yet.

        This is a safety net so enrichment is matched even when the in-process
        ``add_pending_ids`` notification did not reach the matcher loop
        (e.g. across uvicorn workers or a timing race).
        """
        with self.get_db() as db:
            rows = db.fetchAll(
                """
                SELECT DISTINCT j.id FROM jobs j
                LEFT JOIN watcher_match wm
                  ON wm.job_id = j.id AND wm.deleted = 0
                WHERE j.ai_enriched = 1
                  AND j.modified >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
                  AND wm.job_id IS NULL
                """,
                (since_minutes,),
            )
        return [int(r[0]) for r in rows]

    def invalidate_view(self, config_id: int) -> None:
        """Clear watcher_match rows for a config (called when filter config changes)."""
        with self.get_db() as db:
            db.executeAndCommit(
                "DELETE FROM watcher_match WHERE config_id = %s",
                (config_id,),
            )

    def invalidate_watcher_view(self, config_id: int) -> None:
        self.invalidate_view(config_id)
