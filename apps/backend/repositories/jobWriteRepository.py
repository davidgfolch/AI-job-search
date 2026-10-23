from typing import Optional
from commonlib.modality_extractor import modalities_to_db
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection


def _db_values(update_data: dict) -> list:
    """Serialize API-level values to their database representation.

    ``modality`` travels as a list (a job can allow several arrangements) but the
    column is a MySQL SET, so it is stored as a comma-separated string.
    """
    return [modalities_to_db(value) if key == 'modality' else value for key, value in update_data.items()]


class JobWriteRepository:
    def get_db(self):
        return MysqlUtil(getConnection())

    def update_job(self, job_id: int, update_data: dict) -> Optional[int]:
        with self.get_db() as db:
            existing = db.fetchOne("SELECT id FROM jobs WHERE id = %s", job_id)
            if not existing:
                return None
            if not update_data:
                return job_id
            set_clauses = [f"`{key}` = %s" for key in update_data]
            params = _db_values(update_data)
            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = %s"
            db.executeAndCommit(query, params)
        return job_id

    def update_jobs_by_ids(self, job_ids: list, update_data: dict) -> int:
        if not job_ids or not update_data:
            return 0
        with self.get_db() as db:
            set_clauses = [f"`{key}` = %s" for key in update_data]
            params = _db_values(update_data)
            ids = ", ".join(["%s"] * len(job_ids))
            params.extend(job_ids)
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id IN ({ids})"
            db.executeAndCommit(query, params)
            return len(job_ids)

    def update_jobs_by_filter(
        self, where_clauses: list, params: list, update_data: dict
    ) -> int:
        if not update_data:
            return 0
        with self.get_db() as db:
            set_clauses = [f"`{key}` = %s" for key in update_data]
            full_params = _db_values(update_data) + params
            where_str = " AND ".join(where_clauses)
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE {where_str}"
            return db.executeAndCommit(query, full_params)

    def create_job(self, job_data: dict) -> int:
        with self.get_db() as db:
            return db.insertJob(job_data)
