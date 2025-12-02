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
):
    offset = (page - 1) * size
    
    # Build query
    # This is a simplified version. In a real app we'd use a query builder or ORM.
    # Reusing commonlib logic might be tricky if it's too tied to Streamlit state.
    # We'll implement basic SQL construction here.
    
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
            
    where_str = " AND ".join(where_clauses)
    
    # Count total
    count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_str}"
    
    db = get_db()
    total = db.count(count_query, params)
    
    # Fetch items
    # We need to list all columns to match the model
    # For simplicity, we'll select * and let Pydantic handle mapping if names match
    # But names in DB might be slightly different or we need specific order.
    # Let's select * for now.
    query = f"SELECT * FROM jobs WHERE {where_str} ORDER BY created DESC LIMIT %s OFFSET %s"
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
    db = get_db()
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
    db = get_db()
    
    # Check if exists
    if not db.jobExists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Build update query
    update_data = job_update.model_dump(exclude_unset=True)
    if not update_data:
        # Nothing to update, return current
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
