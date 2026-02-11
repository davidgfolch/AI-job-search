from typing import Tuple
from utils.filter_parser import BOOLEAN_FILTER_KEYS
from repositories.queries.jobs_query_builder import (
    get_search_conditions,
    get_days_old_condition,
    get_salary_condition,
    get_salary_condition,
    get_boolean_condition
)

def _quote(val):
    return f"'{str(val)}'"

def _get_view_name(config_id: int) -> str:
    return f"config_view_{config_id}"

def generate_config_view_sql(config_id: int, filters: dict) -> Tuple[str, str]:    
    where_part = _get_where(filters)
    view_name = _get_view_name(config_id)
    sql = f"""
    CREATE OR REPLACE VIEW {view_name} AS
    SELECT 
        {config_id} AS config_id,
        jobs.id AS job_id,
        jobs.created AS job_created
    FROM jobs 
    WHERE {where_part}
    """
    return sql, view_name

def drop_config_view_sql(config_id: int) -> str:
    return f"DROP VIEW IF EXISTS {_get_view_name(config_id)}"

def _get_where(filters: dict) -> str:
    parts = []
    if search := filters.get('search'):
        parts.append(get_search_conditions(_quote(f"'%{search}%'"), alias='jobs'))
    if salary := filters.get('salary'):
        parts.append(get_salary_condition(_quote(salary), alias='jobs'))
    if days_old := filters.get('days_old'):
        parts.append(get_days_old_condition(str(days_old), alias='jobs'))
    boolean_filters = filters.get('boolean_filters', {})
    for key in BOOLEAN_FILTER_KEYS:
        val = boolean_filters.get(key)
        if val is None:
            val = filters.get(key)
        if val is not None:
            is_true = str(val).lower() == 'true'
            if key == 'duplicated':
                sql = "jobs.duplicated_id IS NOT NULL" if is_true else "jobs.duplicated_id IS NULL"
                parts.append(sql)
            else:
                sql_val = '1' if is_true else '0'
                parts.append(get_boolean_condition(key, sql_val, alias='jobs'))
    _get_where_status(filters.get('status'), parts, True)
    _get_where_status(filters.get('not_status'), parts, False)
    if sql_filter := filters.get('sql_filter'):
        parts.append(f"({sql_filter})")
    if parts:
        return  "\n      AND ".join(parts)
    return "1=1"

def _get_where_status(status: str, parts: list, asTrue: bool):
    if status:
        for s in status.split(','):
            field = s.strip()
            if field == 'duplicated':
                parts.append("jobs.duplicated_id IS " + ("NOT NULL" if asTrue else "NULL"))
            else:
                parts.append(f"jobs.`{field}` = " + ("1" if asTrue else "0"))
