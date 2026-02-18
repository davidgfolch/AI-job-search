from typing import Optional
from commonlib.mysqlUtil import MysqlUtil, getConnection


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
            set_clauses = []
            params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                params.append(value)
            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = %s"
            db.executeAndCommit(query, params)
        return job_id

    def update_jobs_by_ids(self, job_ids: list, update_data: dict) -> int:
        if not job_ids or not update_data:
            return 0
        with self.get_db() as db:
            set_clauses = []
            params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                params.append(value)
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
            set_clauses = []
            update_params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                update_params.append(value)
            full_params = update_params + params
            where_str = " AND ".join(where_clauses)
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE {where_str}"
            return db.executeAndCommit(query, full_params)

    def create_job(self, job_data: dict) -> int:
        with self.get_db() as db:
            return db.insertJob(job_data)
