from typing import List, Optional, Dict, Any, Tuple

def build_jobs_where_clause(
    search: Optional[str], 
    status: Optional[str], 
    not_status: Optional[str],
    days_old: Optional[int], 
    salary: Optional[str], 
    sql_filter: Optional[str],
    boolean_filters: Dict[str, Optional[bool]], 
    ids: Optional[List[int]] = None
) -> Tuple[List[str], List[Any]]:
    
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

def parse_job_order(order: Optional[str]) -> Tuple[str, str]:
    allowed_sort_columns = ["created", "modified", "salary", "title", "company", "cv_match_percentage"]
    sort_col, sort_dir = "created", "desc"
    
    if order:
        parts = order.split()
        if len(parts) >= 1 and parts[0] in allowed_sort_columns:
            sort_col = parts[0]
        if len(parts) >= 2 and parts[1].lower() in ["asc", "desc"]:
            sort_dir = parts[1].lower()
            
    return sort_col, sort_dir
