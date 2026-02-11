from typing import List, Optional, Dict, Any, Tuple

# Reusable filter condition generators
def _col(name: str, alias: str) -> str:
    return f"{alias}.{name}" if alias else f"`{name}`" if "." not in name else name

def get_search_conditions(search_term_provider: str, alias: str = "") -> str:
    """
    Returns SQL condition for search.
    Args:
        search_term_provider: SQL snippet that provides the search term
        alias: Table alias for columns (e.g. 'j')
    """
    title_col = _col("title", alias)
    comp_col = _col("company", alias)
    t = f"{alias}.title" if alias else "title"
    c = f"{alias}.company" if alias else "company"
    return f"({t} LIKE {search_term_provider} OR {c} LIKE {search_term_provider})"

def get_days_old_condition(days_provider: str, alias: str = "") -> str:
    col = f"{alias}.created" if alias else "created"
    return f"DATE({col}) >= DATE_SUB(CURDATE(), INTERVAL {days_provider} DAY)"

def get_salary_condition(salary_provider: str, alias: str = "") -> str:
    col = f"{alias}.salary" if alias else "salary"
    return f"({salary_provider} IS NOT NULL AND {col} RLIKE {salary_provider})"

def get_boolean_condition(field_name: str, value_provider: str, alias: str = "") -> str:
    """
    Args:
        field_name: Column name
        value_provider: SQL snippet providing the value
        alias: Table alias
    """
    if alias:
        return f"{alias}.`{field_name}` = {value_provider}"
    return f"`{field_name}` = {value_provider}"

def build_jobs_where_clause(
    search: Optional[str], 
    status: Optional[str], 
    not_status: Optional[str],
    days_old: Optional[int], 
    salary: Optional[str], 
    sql_filter: Optional[str],
    boolean_filters: Dict[str, Optional[bool]], 
    ids: Optional[List[int]] = None,
    created_after: Optional[str] = None, # Expecting ISO string or datetime compatible string
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Tuple[List[str], List[Any]]:
    where = []
    params = []
    if search:
        where.append(get_search_conditions("%s"))
        params.extend([f"%{search}%", f"%{search}%"])
    if status:
        statuses = status.split(',')
        for s in statuses:
            field = s.strip()
            if field == 'duplicated':
                where.append("duplicated_id IS NOT NULL")
            else:
                where.append(f"`{field}` = 1")
    if not_status:
        statuses = not_status.split(',')
        for s in statuses:
            field = s.strip()
            if field == 'duplicated':
                where.append("duplicated_id IS NULL")
            else:
                where.append(f"`{field}` = 0")
    if days_old:
        where.append(get_days_old_condition("%s"))
        params.append(days_old)
    if salary:
        where.append(get_salary_condition("%s"))
        params.extend([salary, salary])
    if sql_filter:
        where.append(f"({sql_filter})")
    if boolean_filters:
        for field_name, field_value in boolean_filters.items():
            if field_value is not None:
                if field_name == 'duplicated':
                    where.append("duplicated_id IS NOT NULL" if field_value else "duplicated_id IS NULL")
                else:
                    val = 1 if field_value else 0
                    where.append(get_boolean_condition(field_name, str(val)))
    if ids:
        placeholders = ', '.join(['%s'] * len(ids))
        where.append(f"id IN ({placeholders})")
        params.extend(ids)
    if created_after:
        where.append("created > %s")
        params.append(created_after)
    if start_date:
        where.append("created >= %s")
        params.append(start_date)
    if end_date:
        where.append("created <= %s")
        params.append(end_date)
    if len(where) == 0:
        where.append("1=1")
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
