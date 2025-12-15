from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection, SELECT_APPLIED_JOB_IDS_BY_COMPANY, SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT, SELECT_APPLIED_JOB_ORDER_BY
from commonlib.sqlUtil import scapeRegexChars, avoidInjection

class JobsRepository:
    def get_db(self):
        return MysqlUtil(getConnection())

    def list_jobs(self, page: int, size: int, search: Optional[str] = None, status: Optional[str] = None,
        not_status: Optional[str] = None, days_old: Optional[int] = None, salary: Optional[str] = None,
        order: Optional[str] = "created desc", boolean_filters: Dict[str, Optional[bool]] = None,
        sql_filter: Optional[str] = None, ids: Optional[List[int]] = None) -> Dict[str, Any]:
        offset = (page - 1) * size
        where, params = self.build_where(search, status, not_status, days_old, salary, sql_filter, boolean_filters, ids)
        where = " AND ".join(where)
        with self.get_db() as db:
            total = self._count_jobs(db, where, params)
            items = self._fetch_jobs(db, where, params, order, size, offset)
        return { "items": items, "total": total, "page": page, "size": size }

    def build_where(self, search: Optional[str], status: Optional[str], not_status: Optional[str],
        days_old: Optional[int], salary: Optional[str], sql_filter: Optional[str],
        boolean_filters: Dict[str, Optional[bool]], ids: Optional[List[int]] = None):
        where = ["1=1"]
        params = []
        if search:
            where.append("(title LIKE %s OR company LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        if status:
            statuses = status.split(',')
            for s in statuses:
                where.append(f"`{s.strip()}` = 1")
        if not_status:
            statuses = not_status.split(',')
            for s in statuses:
                where.append(f"`{s.strip()}` = 0")
        if days_old:
            where.append("DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)")
            params.append(days_old)
        if salary:
            where.append("salary RLIKE %s")
            params.append(salary)
        if sql_filter:
            where.append(f"({sql_filter})")
        if boolean_filters:
            for field_name, field_value in boolean_filters.items():
                if field_value is not None:
                    where.append(f"`{field_name}` = {1 if field_value else 0}")
        if ids:
            placeholders = ', '.join(['%s'] * len(ids))
            where.append(f"id IN ({placeholders})")
            params.extend(ids)
        return where, params

    def _count_jobs(self, db: MysqlUtil, where: str, params: list):
        return db.count(f"SELECT COUNT(*) FROM jobs WHERE {where}", params)

    def _fetch_jobs(self, db: MysqlUtil, where: str, params: list, order: Optional[str], size: int, offset: int):
        sort_col, sort_dir = self._parse_order(order)
        query = f"SELECT * FROM jobs WHERE {where} ORDER BY {sort_col} {sort_dir} LIMIT %s OFFSET %s"
        params_with_limit = params + [size, offset]
        rows = db.fetchAll(query, params_with_limit)
        columns = [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
        items = []
        for row in rows:
            item_dict = {col: val for col, val in zip(columns, row)}
            items.append(item_dict)
        return items

    def _parse_order(self, order: Optional[str]):
        allowed_sort_columns = ["created", "modified", "salary", "title", "company", "cv_match_percentage"]
        sort_col, sort_dir = "created", "desc"
        if order:
            parts = order.split()
            if len(parts) >= 1 and parts[0] in allowed_sort_columns:
                sort_col = parts[0]
            if len(parts) >= 2 and parts[1].lower() in ["asc", "desc"]:
                sort_dir = parts[1].lower()
        return sort_col, sort_dir

    def fetch_job_row(self, db: MysqlUtil, job_id: int) -> Optional[tuple]:
        query = "SELECT * FROM jobs WHERE id = %s"
        return db.fetchOne(query, job_id)

    def fetch_columns(self, db: MysqlUtil) -> List[str]:
        return [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> Optional[int]:
        with self.get_db() as db:
            check_query = "SELECT id FROM jobs WHERE id = %s"
            existing = db.fetchOne(check_query, job_id)
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

    def update_jobs_by_ids(self, job_ids: List[int], update_data: Dict[str, Any]) -> int:
        if not job_ids or not update_data:
            return 0
        
        with self.get_db() as db:
            set_clauses = []
            params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                params.append(value)
            
            placeholders = ', '.join(['%s'] * len(job_ids))
            params.extend(job_ids)
            
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id IN ({placeholders})"
            db.executeAndCommit(query, params)
            return len(job_ids)

    def update_jobs_by_filter(self, where_clauses: List[str], params: List[Any], update_data: Dict[str, Any]) -> int:
        if not update_data:
            return 0
            
        with self.get_db() as db:
            set_clauses = []
            update_params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                update_params.append(value)
            
            # Combine update params with where clause params
            full_params = update_params + params
            where_str = " AND ".join(where_clauses)
            
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE {where_str}"
            db.executeAndCommit(query, full_params)
            # Row count might not be accurate for matched rows vs changed rows in MySQL, but it's okay for now.
            # Ideally we'd select count first if we need the exact number of matched rows.
            return db.cursor.rowcount if hasattr(db, 'cursor') and db.cursor else 0


    def find_applied_by_company(self, company: str, client: str = None) -> List[tuple]:
        avoidInjection(company, "company")
        if client:
            avoidInjection(client, "client")
        regex_lookup = scapeRegexChars(company)
        return self.find_applied_jobs_by_regex(regex_lookup, client)

    def find_applied_jobs_by_regex(self, regex_lookup: str, client_filter: str = None) -> List[tuple]:
        with self.get_db() as db:
            if client_filter:
                qry = SELECT_APPLIED_JOB_IDS_BY_COMPANY
                qry += SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT
                qry += SELECT_APPLIED_JOB_ORDER_BY
                params = {'company': regex_lookup, 'id': '0', 'client': client_filter}
            else:
                qry = SELECT_APPLIED_JOB_IDS_BY_COMPANY + SELECT_APPLIED_JOB_ORDER_BY
                params = {'company': regex_lookup, 'id': '0'}
            return db.fetchAll(qry.format(**params))
