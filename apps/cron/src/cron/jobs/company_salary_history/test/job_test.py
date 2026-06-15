from unittest.mock import MagicMock, patch
from cron.jobs.company_salary_history.job import CompanySalaryHistoryJob


def test_job_has_name_and_cadency():
    job = CompanySalaryHistoryJob(cadency="1h")
    assert job.name == "companySalaryHistory"
    assert job.cadency == "1h"

@patch("cron.jobs.company_salary_history.job.CompanySalaryHistoryScanner")
@patch("cron.jobs.company_salary_history.job.SalaryHistoryRepository")
@patch("cron.jobs.company_salary_history.job.get_mongo_provider")
def test_job_run_with_prior_state(mock_get_mongo, mock_salary_repo_cls, mock_scanner_cls):
    mock_scanner = MagicMock()
    mock_scanner.run.return_value = {"last_job_id": 10, "records_added": 3}
    mock_scanner_cls.return_value = mock_scanner
    mock_cron_state = MagicMock()
    mock_cron_state.get_state.return_value = {"last_job_id": 5, "last_run_at": "2024-01-01"}

    job = CompanySalaryHistoryJob(cadency="1h")
    job.run(mock_cron_state)

    mock_scanner.run.assert_called_once_with(last_job_id=5, last_run_at="2024-01-01")
    mock_cron_state.update_state.assert_called_once_with("companySalaryHistory", {"last_job_id": 10})

@patch("cron.jobs.company_salary_history.job.CompanySalaryHistoryScanner")
@patch("cron.jobs.company_salary_history.job.SalaryHistoryRepository")
@patch("cron.jobs.company_salary_history.job.get_mongo_provider")
def test_job_run_no_prior_state(mock_get_mongo, mock_salary_repo_cls, mock_scanner_cls):
    mock_scanner = MagicMock()
    mock_scanner.run.return_value = {"last_job_id": 5, "records_added": 0}
    mock_scanner_cls.return_value = mock_scanner
    mock_cron_state = MagicMock()
    mock_cron_state.get_state.return_value = None

    job = CompanySalaryHistoryJob(cadency="1h")
    job.run(mock_cron_state)

    mock_scanner.run.assert_called_once_with(last_job_id=0, last_run_at=None)
    mock_cron_state.update_state.assert_called_once_with("companySalaryHistory", {"last_job_id": 5})
