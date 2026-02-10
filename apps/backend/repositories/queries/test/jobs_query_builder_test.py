import pytest
from repositories.queries.jobs_query_builder import build_jobs_where_clause, parse_job_order

@pytest.mark.parametrize("search, expected_clause_part, expected_param_count", [
    ("developer", "(title LIKE %s OR company LIKE %s)", 2),
    (None, None, 0),
])
def test_build_jobs_where_clause_search(search, expected_clause_part, expected_param_count):
    where, params = build_jobs_where_clause(
        search=search, status=None, not_status=None, days_old=None, 
        salary=None, sql_filter=None, boolean_filters={}
    )
    
    if expected_clause_part:
        assert any(expected_clause_part in w for w in where)
        assert len(params) == expected_param_count
    else:
        assert len(where) == 1 # Just "1=1"
        assert len(params) == 0

@pytest.mark.parametrize("status, expected_clauses", [
    ("seen", ["`seen` = 1"]),
    ("seen,applied", ["`seen` = 1", "`applied` = 1"]),
    (None, []),
])
def test_build_jobs_where_clause_status(status, expected_clauses):
    where, _ = build_jobs_where_clause(
        search=None, status=status, not_status=None, days_old=None, 
        salary=None, sql_filter=None, boolean_filters={}
    )
    for clause in expected_clauses:
        assert clause in where

@pytest.mark.parametrize("order_input, expected_col, expected_dir", [
    ("salary asc", "salary", "asc"),
    ("created desc", "created", "desc"),
    ("invalid asc", "created", "asc"), # Default col, valid dir
    (None, "created", "desc"),
])
def test_parse_job_order(order_input, expected_col, expected_dir):
    col, dir = parse_job_order(order_input)
    assert col == expected_col
    assert dir == expected_dir

def test_build_jobs_where_clause_created_after():
    """Test building where clause with created_after"""
    where, params = build_jobs_where_clause(
        search=None, status=None, not_status=None, days_old=None, 
        salary=None, sql_filter=None, boolean_filters={},
        created_after="2023-01-01T12:00:00"
    )
    
    assert "created > %s" in where
    assert "2023-01-01T12:00:00" in params

@pytest.mark.parametrize("boolean_filters, expected_clauses", [
    ({"merged": True}, ["merged IS NOT NULL"]),
    ({"merged": False}, ["merged IS NULL"]),
    ({"flagged": True}, ["`flagged` = 1"]),
], ids=["merged_true", "merged_false", "flagged_true"])
def test_build_jobs_where_clause_boolean_filters(boolean_filters, expected_clauses):
    where, _ = build_jobs_where_clause(
        search=None, status=None, not_status=None, days_old=None, 
        salary=None, sql_filter=None, boolean_filters=boolean_filters
    )
    for clause in expected_clauses:
        assert clause in where
