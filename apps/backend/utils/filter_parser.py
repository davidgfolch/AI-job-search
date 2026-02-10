"""
Filter parsing utilities for consistent filter extraction across the backend.

This module provides shared utilities for parsing filter dictionaries into
the format expected by the query builder, ensuring DRY principles across
services, repositories, and API handlers.
"""

from typing import Dict, Optional, List, Any, Tuple

# Boolean filter keys - single source of truth
BOOLEAN_FILTER_KEYS = [
    'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded', 'closed',
    'interview_rh', 'interview', 'interview_tech', 'interview_technical_test',
    'interview_technical_test_done', 'ai_enriched', 'easy_apply', 'duplicated'
]

# Backward compatibility alias
JOB_BOOLEAN_KEYS = BOOLEAN_FILTER_KEYS


def extract_boolean_filters(filters: Dict[str, Any], keys: Optional[List[str]] = None) -> Dict[str, Optional[bool]]:
    """
    Extract boolean filters from a filters dictionary.

    Only includes keys that are present in the filters dictionary.

    Args:
        filters: Dictionary containing filter parameters
        keys: Optional list of keys to extract. Defaults to BOOLEAN_FILTER_KEYS

    Returns:
        Dictionary with only the boolean keys that exist in filters
    """
    if keys is None:
        keys = BOOLEAN_FILTER_KEYS

    return {k: filters.get(k) for k in keys if k in filters}


def extract_filter_params(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all standard filter parameters from a filters dictionary.

    Args:
        filters: Dictionary containing filter parameters

    Returns:
        Dictionary with all standard filter parameters including parsed boolean filters
    """
    boolean_filters = extract_boolean_filters(filters)

    return {
        'search': filters.get('search'),
        'status': filters.get('status'),
        'not_status': filters.get('not_status'),
        'days_old': filters.get('days_old'),
        'salary': filters.get('salary'),
        'sql_filter': filters.get('sql_filter'),
        'boolean_filters': boolean_filters,
        'ids': filters.get('ids'),
        'created_after': filters.get('created_after')
    }


def build_where_params(
    search: Optional[str] = None,
    status: Optional[str] = None,
    not_status: Optional[str] = None,
    days_old: Optional[int] = None,
    salary: Optional[str] = None,
    sql_filter: Optional[str] = None,
    boolean_filters: Optional[Dict[str, Optional[bool]]] = None,
    ids: Optional[List[int]] = None,
    created_after: Optional[str] = None
) -> Tuple[List[str], List[Any]]:
    """
    Build WHERE clause clauses and parameters from filter parameters.

    This is a wrapper around the repository's build_where functionality
    that can be used independently when needed.

    Args:
        search: Search term for title/company
        status: Status filter (comma-separated)
        not_status: Negative status filter (comma-separated)
        days_old: Filter jobs younger than N days
        salary: Salary regex filter
        sql_filter: Raw SQL filter
        boolean_filters: Dictionary of boolean field filters
        ids: List of specific job IDs
        created_after: Filter jobs created after this timestamp

    Returns:
        Tuple of (where_clauses, params) for use in SQL queries
    """
    # Import here to avoid circular dependencies
    from repositories.queries.jobs_query_builder import build_jobs_where_clause

    return build_jobs_where_clause(
        search=search,
        status=status,
        not_status=not_status,
        days_old=days_old,
        salary=salary,
        sql_filter=sql_filter,
        boolean_filters=boolean_filters or {},
        ids=ids,
        created_after=created_after
    )
