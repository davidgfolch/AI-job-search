"""Backward-compatible re-exports of the shared job filter builder.

The implementation lives in `commonlib.sql.job_filter_builder` so the AI
enrichment workers can reuse the exact same filtering/ordering logic as the
backend. Import from here to keep the backend call sites unchanged.
"""

from commonlib.sql.job_filter_builder import (  # noqa: F401
    BOOLEAN_FILTER_KEYS,
    build_jobs_where_clause,
    get_boolean_condition,
    get_days_old_condition,
    get_modality_condition,
    get_salary_condition,
    get_search_conditions,
    parse_job_order,
)

__all__ = [
    "BOOLEAN_FILTER_KEYS",
    "build_jobs_where_clause",
    "get_boolean_condition",
    "get_days_old_condition",
    "get_modality_condition",
    "get_salary_condition",
    "get_search_conditions",
    "parse_job_order",
]
