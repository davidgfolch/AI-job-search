from typing import Optional
from commonlib.mysqlUtil import MysqlUtil, getConnection
from repositories.queries.jobs_query_builder import (
    build_jobs_where_clause,
    parse_job_order,
)


class JobReadRepository:
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
        boolean_filters: Optional[dict] = None,
        sql_filter: Optional[str] = None,
        ids: Optional[list] = None,
        created_after: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
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
        boolean_filters: Optional[dict] = None,
        sql_filter: Optional[str] = None,
        ids: Optional[list] = None,
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

    def _count_jobs(self, db: MysqlUtil, where: str, params: list) -> int:
        return db.count(f"SELECT COUNT(*) FROM jobs WHERE {where}", params)

    def _fetch_jobs(
        self,
        db: MysqlUtil,
        where: str,
        params: list,
        order: str,
        size: int,
        offset: int,
    ) -> list:
        sort_col, sort_dir = parse_job_order(order)
        query = f"SELECT * FROM jobs WHERE {where} ORDER BY {sort_col} {sort_dir}, id DESC LIMIT %s OFFSET %s"
        rows = db.fetchAll(query, params + [size, offset])
        columns = [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
        return [dict(zip(columns, row)) for row in rows]

    def fetch_job_row(self, db: MysqlUtil, job_id: int) -> Optional[tuple]:
        return db.fetchOne("SELECT * FROM jobs WHERE id = %s", job_id)

    def fetch_columns(self, db: MysqlUtil) -> list:
        return [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
