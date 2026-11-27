from unittest.mock import MagicMock, patch
import pytest
from cron.jobs.company_salary_history.scanner import CompanySalaryHistoryScanner


def make_scanner(salary_rows=None, updated_rows=None):
    salary_repo = MagicMock()
    job_repo = MagicMock()
    job_repo.fetch_salary_jobs_after.return_value = salary_rows or []
    job_repo.fetch_updated_salary_jobs.return_value = updated_rows or []
    salary_repo.save_records.return_value = len(salary_rows or [])
    return CompanySalaryHistoryScanner(salary_repo, job_repo), salary_repo, job_repo


def test_scanner_imports():
    assert CompanySalaryHistoryScanner is not None


@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
def test_scanner_no_new_jobs(_mock_normalize):
    scanner, salary_repo, job_repo = make_scanner()
    assert scanner.run(last_job_id=5) == {"last_job_id": 5, "records_added": 0}
    salary_repo.save_records.assert_not_called()
    job_repo.fetch_salary_jobs_after.assert_called_once_with(5)


@pytest.mark.parametrize("last_job_id, expected_source", [(0, "backfill"), (5, "incremental")], ids=["backfill", "incremental"])
@patch("cron.jobs.company_salary_history.scanner.normalize_company_name", return_value="acme")
def test_scanner_new_jobs(mock_normalize, last_job_id, expected_source):
    rows = [(1, "Engineer", "Acme Inc", "100k", "2024-01-01"), (2, "Manager", "Beta Corp", "120k", "2024-01-02")]
    scanner, salary_repo, _ = make_scanner(salary_rows=rows)
    result = scanner.run(last_job_id=last_job_id)
    assert result == {"last_job_id": max(last_job_id, 2), "records_added": 2}
    records = salary_repo.save_records.call_args[0][0]
    assert [r["source"] for r in records] == [expected_source, expected_source]
    assert records[0]["company_normalized"] == "acme"
    assert mock_normalize.call_count == 2


@pytest.mark.parametrize("prior_salary, expected_added", [("90k", 2), ("100k", 1), (None, 2)], ids=["changed", "unchanged", "no_prior"])
@patch("cron.jobs.company_salary_history.scanner.normalize_company_name", return_value="acme")
def test_scanner_updated_jobs(mock_normalize, prior_salary, expected_added):
    scanner, salary_repo, job_repo = make_scanner(
        salary_rows=[(1, "Engineer", "Acme Inc", "90k", "2024-01-01")],
        updated_rows=[(1, "Engineer", "Acme Inc", "100k", "2024-01-15")],
    )
    salary_repo.get_last_record.return_value = None if prior_salary is None else {"salary": prior_salary}
    result = scanner.run(last_job_id=1, last_run_at="2024-01-10")
    assert result["records_added"] == expected_added
    job_repo.fetch_updated_salary_jobs.assert_called_once_with("2024-01-10", 1)
    if prior_salary == "100k":
        salary_repo.save_record.assert_not_called()
    else:
        salary_repo.save_record.assert_called_once()
        assert salary_repo.save_record.call_args[0][0]["source"] == "incremental"


@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
def test_scanner_last_run_at_no_updates(_mock_normalize):
    scanner, _, job_repo = make_scanner()
    assert scanner.run(last_job_id=5, last_run_at="2024-01-10") == {"last_job_id": 5, "records_added": 0}
    job_repo.fetch_updated_salary_jobs.assert_called_once_with("2024-01-10", 5)
