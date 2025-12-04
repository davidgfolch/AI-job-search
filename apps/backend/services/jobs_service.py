from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection

class JobsService:
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
    ) -> Dict[str, Any]:
        offset = (page - 1) * size
        
        # Build query
        where_clauses = ["1=1"]
        params = []
        
        if search:
            # Simple search in title or company
            where_clauses.append("(title LIKE %s OR company LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
            
        if status:
            statuses = status.split(',')
            for s in statuses:
                where_clauses.append(f"`{s.strip()}` = 1")
                
        if not_status:
            statuses = not_status.split(',')
            for s in statuses:
                where_clauses.append(f"`{s.strip()}` = 0")

        if days_old:
            where_clauses.append("DATE(created) >= DATE_SUB(CURDATE(), INTERVAL %s DAY)")
            params.append(days_old)

        if salary:
            where_clauses.append("salary RLIKE %s")
            params.append(salary)

        if sql_filter:
            where_clauses.append(f"({sql_filter})")
        
        if boolean_filters:
            for field_name, field_value in boolean_filters.items():
                if field_value is not None:
                    where_clauses.append(f"`{field_name}` = {1 if field_value else 0}")
                
        where_str = " AND ".join(where_clauses)
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_str}"
        
        with self.get_db() as db:
            total = db.count(count_query, params)
            
            # Fetch items
            # Validate order to prevent SQL injection
            allowed_sort_columns = ["created", "modified", "salary", "title", "company", "cv_match_percentage"]
            sort_col, sort_dir = "created", "desc"
            
            if order:
                parts = order.split()
                if len(parts) >= 1 and parts[0] in allowed_sort_columns:
                    sort_col = parts[0]
                if len(parts) >= 2 and parts[1].lower() in ["asc", "desc"]:
                    sort_dir = parts[1].lower()
                    
            query = f"SELECT * FROM jobs WHERE {where_str} ORDER BY {sort_col} {sort_dir} LIMIT %s OFFSET %s"
            
            params_with_limit = params + [size, offset]
            
            rows = db.fetchAll(query, params_with_limit)
            # Get raw column names without translation
            columns = [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
            
            items = []
            for row in rows:
                # Use raw column names (they're already lowercase in MySQL)
                item_dict = {col: val for col, val in zip(columns, row)}
                items.append(item_dict)
            
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.get_db() as db:
            query = "SELECT * FROM jobs WHERE id = %s"
            row = db.fetchOne(query, job_id)
            
            if not row:
                return None
                
            # Get raw column names without translation
            columns = [col[0] for col in db.fetchAll("SHOW COLUMNS FROM jobs")]
            # Use raw column names (they're already lowercase in MySQL)
            item_dict = {col: val for col, val in zip(columns, row)}
            return item_dict

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.get_db() as db:
            # Check if exists
            check_query = "SELECT id FROM jobs WHERE id = %s"
            existing = db.fetchOne(check_query, job_id)
            if not existing:
                return None
                
            if not update_data:
                return self.get_job(job_id)
                
            set_clauses = []
            params = []
            for key, value in update_data.items():
                set_clauses.append(f"`{key}` = %s")
                params.append(value)
                
            params.append(job_id)
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = %s"
            
            db.executeAndCommit(query, params)
            
        return self.get_job(job_id)
