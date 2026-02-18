from typing import List, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection


class JobDeleteRepository:
    def __init__(self, mysql: MysqlUtil = None):
        self._mysql = mysql

    def get_db(self) -> MysqlUtil:
        if self._mysql:
            return self._mysql
        return MysqlUtil(getConnection())

    def delete_jobs_by_ids(self, job_ids: List[int]) -> int:
        if not job_ids:
            return 0
        with self.get_db() as db:
            ids = ", ".join(["%s"] * len(job_ids))
            query = f"DELETE FROM jobs WHERE id IN ({ids})"
            return db.executeAndCommit(query, job_ids)

    def delete_jobs_by_filter(self, where_clauses: List[str], params: List[Any]) -> int:
        with self.get_db() as db:
            where_str = " AND ".join(where_clauses)
            query = f"DELETE FROM jobs WHERE {where_str}"
            return db.executeAndCommit(query, params)

    def delete_jobs_with_snapshots(
        self, where_clauses: List[str], params: List[Any], snapshot_queries: List[tuple]
    ) -> int:
        with self.get_db() as db:
            where_str = " AND ".join(where_clauses)
            get_query = f"SELECT * FROM jobs WHERE {where_str}"
            rows = db.fetchAll(get_query, params)
            columns = [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
            items = []
            for row in rows:
                item_dict = {col: val for col, val in zip(columns, row)}
                items.append(item_dict)

            queries = []
            for snapshot_query, snapshot_params in snapshot_queries:
                queries.append({"query": snapshot_query, "params": snapshot_params})

            delete_query = f"DELETE FROM jobs WHERE {where_str}"
            queries.append({"query": delete_query, "params": params})

            db.executeAllAndCommit(queries)
            return len(items)

    def get_jobs_by_filter(
        self, where_clauses: List[str], params: List[Any]
    ) -> List[Dict[str, Any]]:
        with self.get_db() as db:
            where_str = " AND ".join(where_clauses)
            query = f"SELECT * FROM jobs WHERE {where_str}"
            rows = db.fetchAll(query, params)
            columns = [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
            items = []
            for row in rows:
                item_dict = {col: val for col, val in zip(columns, row)}
                items.append(item_dict)
            return items

    def update_jobs_by_ids(
        self, job_ids: List[int], update_data: Dict[str, Any]
    ) -> int:
        if not job_ids:
            return 0
        with self.get_db() as db:
            set_clauses = []
            update_params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                update_params.append(value)
            ids = ", ".join(["%s"] * len(job_ids))
            params = update_params + job_ids
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id IN ({ids})"
            return db.executeAndCommit(query, params)

    def update_jobs_by_filter(
        self, where_clauses: List[str], params: List[Any], update_data: Dict[str, Any]
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
