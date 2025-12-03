from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from commonlib.mysqlUtil import MysqlUtil, getConnection
from models.job import Job, JobUpdate, JobListResponse

router = APIRouter()

# Helper to get DB connection
def get_db():
    return MysqlUtil(getConnection())

@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,  # e.g. "applied,interview"
    not_status: Optional[str] = None, # e.g. "discarded,closed"
    days_old: Optional[int] = None,
    salary: Optional[str] = None,
    order: Optional[str] = "created desc",
    # Boolean field filters
    flagged: Optional[bool] = None,
    like: Optional[bool] = None,
    ignored: Optional[bool] = None,
    seen: Optional[bool] = None,
    applied: Optional[bool] = None,
    discarded: Optional[bool] = None,
    closed: Optional[bool] = None,
    interview_rh: Optional[bool] = None,
    interview: Optional[bool] = None,
    interview_tech: Optional[bool] = None,
    interview_technical_test: Optional[bool] = None,
    interview_technical_test_done: Optional[bool] = None,
    ai_enriched: Optional[bool] = None,
    easy_apply: Optional[bool] = None,
    sql_filter: Optional[str] = None,
):
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
    
    # Boolean field filters
    boolean_filters = {
        'flagged': flagged,
        'like': like,
        'ignored': ignored,
        'seen': seen,
        'applied': applied,
        'discarded': discarded,
        'closed': closed,
        'interview_rh': interview_rh,
        'interview': interview,
        'interview_tech': interview_tech,
        'interview_technical_test': interview_technical_test,
        'interview_technical_test_done': interview_technical_test_done,
        'ai_enriched': ai_enriched,
        'easy_apply': easy_apply,
    }
    
    for field_name, field_value in boolean_filters.items():
        if field_value is not None:
            where_clauses.append(f"`{field_name}` = {1 if field_value else 0}")
            
    where_str = " AND ".join(where_clauses)
    
    # Count total
    count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_str}"
    
    with get_db() as db:
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
        # params for limit/offset need to be integers
        # mysql-connector might need them as params or injected if safe.
        # Using params for limit/offset
        
        # Note: mysqlUtil.fetchAll takes params.
        # We need to append limit/offset to params
        params_with_limit = params + [size, offset]
        
        # However, fetchAll returns tuples. We need to map them to dicts.
        # MysqlUtil doesn't seem to return dicts by default unless we use a specific cursor or map it.
        # Let's check MysqlUtil.fetchAll implementation. It uses default cursor.
        # We can use getTableDdlColumnNames to get headers.
        
        rows = db.fetchAll(query, params_with_limit)
        columns = db.getTableDdlColumnNames('jobs')
        
        items = []
        for row in rows:
            # Convert column names to lowercase to match Pydantic model
            item_dict = {col.lower(): val for col, val in zip(columns, row)}
            items.append(item_dict)
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int):
    with get_db() as db:
        # Using fetchOne which returns a dict? 
        # Wait, fetchOne in MysqlUtil:
        # def fetchOne(self, query: str, id: int | str) -> Dict[str, RowItemType]:
        # It takes `id` as a second arg and expects query to have %s.
        # But it returns c.fetchone() which is a tuple.
        # The type hint says Dict but implementation suggests tuple unless cursor is dictionary cursor.
        # Let's check MysqlUtil.cursor().
        # c = conn.cursor() -> default is tuple.
        # So fetchOne returns tuple.
        
        # We need to map it.
        query = "SELECT * FROM jobs WHERE id = %s"
        row = db.fetchOne(query, job_id)
        
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
            
        columns = db.getTableDdlColumnNames('jobs')
        # Convert column names to lowercase to match Pydantic model
        item_dict = {col.lower(): val for col, val in zip(columns, row)}
        return item_dict

@router.patch("/{job_id}", response_model=Job)
def update_job(job_id: int, job_update: JobUpdate):
    with get_db() as db:
        # Check if exists
        if not db.jobExists(job_id):
            raise HTTPException(status_code=404, detail="Job not found")
            
        # Build update query
        update_data = job_update.model_dump(exclude_unset=True)
        if not update_data:
            # Nothing to update, return current
            # Note: get_job will open its own connection, which is fine with pooling
            return get_job(job_id)
            
        set_clauses = []
        params = []
        for key, value in update_data.items():
            set_clauses.append(f"`{key}` = %s")
            params.append(value)
            
        params.append(job_id)
        query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = %s"
        
        db.executeAndCommit(query, params)
        
    return get_job(job_id)
