import json
from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import (
    MysqlUtil,
    getConnection,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT,
    SELECT_APPLIED_JOB_ORDER_BY,
)
from commonlib.sqlUtil import scapeRegexChars, avoidInjection
from repositories.queries.jobs_query_builder import (
    build_jobs_where_clause,
    parse_job_order,
)


class JobsRepository:
    def get_db(self):
        return MysqlUtil(getConnection())

    def list_jobs(
        self,
        page: int,
        size: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        not_status: Optional[str] = None,
        days_old: Optional[int] = None,
        salary: Optional[str] = None,
        order: Optional[str] = "created desc",
        boolean_filters: Dict[str, Optional[bool]] = None,
        sql_filter: Optional[str] = None,
        ids: Optional[List[int]] = None,
        created_after: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        offset = (page - 1) * size
        where_clauses, params = build_jobs_where_clause(
            search,
            status,
            not_status,
            days_old,
            salary,
            sql_filter,
            boolean_filters,
            ids,
            created_after,
            start_date,
            end_date,
        )
        where_str = " AND ".join(where_clauses)
        with self.get_db() as db:
            total = self._count_jobs(db, where_str, params)
            items = self._fetch_jobs(db, where_str, params, order, size, offset)
        return {"items": items, "total": total, "page": page, "size": size}

    def count_jobs(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        not_status: Optional[str] = None,
        days_old: Optional[int] = None,
        salary: Optional[str] = None,
        boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
        sql_filter: Optional[str] = None,
        ids: Optional[List[int]] = None,
        created_after: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> int:
        where_clauses, params = build_jobs_where_clause(
            search,
            status,
            not_status,
            days_old,
            salary,
            sql_filter,
            boolean_filters,
            ids,
            created_after,
            start_date,
            end_date,
        )
        where_str = " AND ".join(where_clauses)
        with self.get_db() as db:
            return self._count_jobs(db, where_str, params)

    def build_where(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        not_status: Optional[str] = None,
        days_old: Optional[int] = None,
        salary: Optional[str] = None,
        sql_filter: Optional[str] = None,
        boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
        ids: Optional[List[int]] = None,
        created_after: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        return build_jobs_where_clause(
            search,
            status,
            not_status,
            days_old,
            salary,
            sql_filter,
            boolean_filters,
            ids,
            created_after,
            start_date,
            end_date,
        )

    def _count_jobs(self, db: MysqlUtil, where: str, params: list):
        return db.count(f"SELECT COUNT(*) FROM jobs WHERE {where}", params)

    def _fetch_jobs(
        self,
        db: MysqlUtil,
        where: str,
        params: list,
        order: Optional[str],
        size: int,
        offset: int,
    ):
        sort_col, sort_dir = parse_job_order(order)
        query = f"SELECT * FROM jobs WHERE {where} ORDER BY {sort_col} {sort_dir}, id DESC LIMIT %s OFFSET %s"
        rows = db.fetchAll(query, params + [size, offset])
        if rows is None:
            return []
            
        columns_data = db.fetchAll("SHOW COLUMNS FROM jobs")
        if not columns_data:
            return []
        columns = [col[0] for col in columns_data]
        return [dict(zip(columns, row)) for row in rows]

    def fetch_job_row(self, db: MysqlUtil, job_id: int) -> Optional[tuple]:
        return db.fetchOne("SELECT * FROM jobs WHERE id = %s", job_id)

    def fetch_columns(self, db: MysqlUtil) -> List[str]:
        return [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> Optional[int]:
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

    def update_jobs_by_ids(
        self, job_ids: List[int], update_data: Dict[str, Any]
    ) -> int:
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

    def create_job(self, job_data: Dict[str, Any]) -> int:
        with self.get_db() as db:
            return db.insertJob(job_data)
