from unittest.mock import MagicMock
import pytest
from commonlib.repositories.job_salary_repository import JobSalaryRepository, SALARY_JOBS_AFTER_QUERY, UPDATED_SALARY_JOBS_QUERY


@pytest.mark.parametrize("method, args, expected_query, expected_params", [
    ("fetch_salary_jobs_after", (5,), SALARY_JOBS_AFTER_QUERY, (5,)),
    ("fetch_updated_salary_jobs", ("2024-01-01", 10), UPDATED_SALARY_JOBS_QUERY, ("2024-01-01", 10)),
])
def test_salary_queries_delegate_to_mysql(method, args, expected_query, expected_params):
    mysql = MagicMock()
    mysql.fetchAll.return_value = []
    assert getattr(JobSalaryRepository(mysql), method)(*args) == []
    mysql.fetchAll.assert_called_once_with(expected_query, expected_params)


def test_repository_owns_both_job_queries():
    assert "COALESCE(modified, created)" in SALARY_JOBS_AFTER_QUERY
    assert "id > %s" in SALARY_JOBS_AFTER_QUERY
    assert "modified > %s" in UPDATED_SALARY_JOBS_QUERY
    assert "id <= %s" in UPDATED_SALARY_JOBS_QUERY


def test_fetch_returns_all_rows():
    mysql = MagicMock()
    rows = [(1, "Engineer", "Acme", "100k", "2024-01-01")]
    mysql.fetchAll.return_value = rows
    assert JobSalaryRepository(mysql).fetch_salary_jobs_after(0) == rows
