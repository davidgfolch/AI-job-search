import pytest
from commonlib.sql.job_filter_builder import (
    BASE_PENDING_CONDITION,
    build_jobs_where_clause,
    parse_job_order,
    strip_ai_enriched,
)


@pytest.mark.parametrize(
    "search, expected_clause_part, expected_param_count",
    [
        ("developer", "(title LIKE %s OR company LIKE %s)", 2),
        (None, None, 0),
    ],
)
def test_build_jobs_where_clause_search(search, expected_clause_part, expected_param_count):
    where, params = build_jobs_where_clause(
        search=search, status=None, not_status=None, days_old=None,
        salary=None, sql_filter=None, boolean_filters={},
    )
    if expected_clause_part:
        assert any(expected_clause_part in w for w in where)
        assert len(params) == expected_param_count
    else:
        assert where == ["1=1"]
        assert params == []


@pytest.mark.parametrize(
    "boolean_filters, expected_clauses",
    [
        ({"duplicated": True}, ["duplicated_id IS NOT NULL"]),
        ({"duplicated": False}, ["duplicated_id IS NULL"]),
        ({"flagged": True}, ["`flagged` = 1"]),
        ({"ai_enriched": True}, ["`ai_enriched` = 1"]),
    ],
    ids=["duplicated_true", "duplicated_false", "flagged_true", "ai_enriched_true"],
)
def test_build_jobs_where_clause_boolean_filters(boolean_filters, expected_clauses):
    where, _ = build_jobs_where_clause(
        search=None, status=None, not_status=None, days_old=None,
        salary=None, sql_filter=None, boolean_filters=boolean_filters,
    )
    for clause in expected_clauses:
        assert clause in where


@pytest.mark.parametrize(
    "order_input, expected_col, expected_dir",
    [
        ("salary asc", "salary", "asc"),
        ("created asc", "created", "asc"),
        ("invalid asc", "created", "asc"),
        (None, "created", "desc"),
    ],
)
def test_parse_job_order(order_input, expected_col, expected_dir):
    assert parse_job_order(order_input) == (expected_col, expected_dir)


def test_base_pending_condition_excludes_enriched_error_ignored_discarded_closed():
    assert "ai_enriched" in BASE_PENDING_CONDITION
    assert "ai_enrich_error" in BASE_PENDING_CONDITION
    for flag in ("ignored", "discarded", "closed"):
        assert flag in BASE_PENDING_CONDITION


def test_strip_ai_enriched_removes_flat_key():
    assert strip_ai_enriched({"ai_enriched": True, "applied": True}) == {"applied": True}


def test_strip_ai_enriched_removes_nested_key():
    clean = strip_ai_enriched({"boolean_filters": {"ai_enriched": True, "seen": False}})
    assert clean == {"boolean_filters": {"seen": False}}


def test_strip_ai_enriched_removes_status_tokens():
    clean = strip_ai_enriched({"status": "ai_enriched,seen", "not_status": "ai_enriched"})
    assert clean == {"status": "seen"}


def test_strip_ai_enriched_does_not_mutate_input():
    original = {"ai_enriched": True}
    strip_ai_enriched(original)
    assert original == {"ai_enriched": True}
