from unittest.mock import MagicMock, patch
from cron.jobs.company_salary_history.scanner import CompanySalaryHistoryScanner


def test_scanner_imports():
    assert CompanySalaryHistoryScanner is not None

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_no_new_jobs(mock_get_conn, mock_mysql_cls, mock_normalize):
    scanner = CompanySalaryHistoryScanner(MagicMock())
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = []
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql

    result = scanner.run(last_job_id=5)

    assert result == {"last_job_id": 5, "records_added": 0}

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_backfill_new_jobs(mock_get_conn, mock_mysql_cls, mock_normalize):
    salary_repo = MagicMock()
    scanner = CompanySalaryHistoryScanner(salary_repo)
    mock_normalize.side_effect = lambda name: name.lower().split()[0]
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = [
        (1, "Engineer", "Acme Inc", "100k", "2024-01-01"),
        (2, "Manager", "Beta Corp", "120k", "2024-01-02"),
    ]
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql
    salary_repo.save_records.return_value = 2

    result = scanner.run(last_job_id=0)

    assert result["last_job_id"] == 2
    assert result["records_added"] == 2
    salary_repo.save_records.assert_called_once()
    records = salary_repo.save_records.call_args[0][0]
    assert records[0]["source"] == "backfill"
    assert records[0]["company_normalized"] == "acme"

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_incremental_new_jobs(mock_get_conn, mock_mysql_cls, mock_normalize):
    salary_repo = MagicMock()
    scanner = CompanySalaryHistoryScanner(salary_repo)
    mock_normalize.return_value = "acme"
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = [
        (10, "Engineer", "Acme Inc", "100k", "2024-06-01"),
    ]
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql
    salary_repo.save_records.return_value = 1

    result = scanner.run(last_job_id=5)

    assert result["last_job_id"] == 10
    assert result["records_added"] == 1
    records = salary_repo.save_records.call_args[0][0]
    assert records[0]["source"] == "incremental"

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_updated_jobs_salary_changed(mock_get_conn, mock_mysql_cls, mock_normalize):
    salary_repo = MagicMock()
    scanner = CompanySalaryHistoryScanner(salary_repo)
    mock_normalize.return_value = "acme"
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.side_effect = [
        [(1, "Engineer", "Acme Inc", "90k", "2024-01-01")],
        [(1, "Engineer", "Acme Inc", "100k", "2024-01-15")],
    ]
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql
    salary_repo.save_records.return_value = 1
    salary_repo.get_last_record.return_value = {"salary": "90k"}

    result = scanner.run(last_job_id=1, last_run_at="2024-01-10")

    assert result["records_added"] == 2
    salary_repo.save_record.assert_called_once()

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_updated_jobs_salary_unchanged(mock_get_conn, mock_mysql_cls, mock_normalize):
    salary_repo = MagicMock()
    scanner = CompanySalaryHistoryScanner(salary_repo)
    mock_normalize.return_value = "acme"
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.side_effect = [
        [],
        [(1, "Engineer", "Acme Inc", "100k", "2024-01-15")],
    ]
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql
    salary_repo.get_last_record.return_value = {"salary": "100k"}

    result = scanner.run(last_job_id=1, last_run_at="2024-01-10")

    assert result["records_added"] == 0
    salary_repo.save_record.assert_not_called()

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_updated_jobs_no_prior_record(mock_get_conn, mock_mysql_cls, mock_normalize):
    salary_repo = MagicMock()
    scanner = CompanySalaryHistoryScanner(salary_repo)
    mock_normalize.return_value = "acme"
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.side_effect = [
        [],
        [(1, "Engineer", "Acme Inc", "100k", "2024-01-15")],
    ]
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql
    salary_repo.get_last_record.return_value = None

    result = scanner.run(last_job_id=1, last_run_at="2024-01-10")

    assert result["records_added"] == 1
    salary_repo.save_record.assert_called_once()

@patch("cron.jobs.company_salary_history.scanner.normalize_company_name")
@patch("cron.jobs.company_salary_history.scanner.MysqlUtil")
@patch("cron.jobs.company_salary_history.scanner.getConnection")
def test_scanner_last_run_at_no_updates(mock_get_conn, mock_mysql_cls, mock_normalize):
    salary_repo = MagicMock()
    scanner = CompanySalaryHistoryScanner(salary_repo)
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.side_effect = [[], []]
    mock_mysql_cls.return_value.__enter__.return_value = mock_mysql

    result = scanner.run(last_job_id=5, last_run_at="2024-01-10")

    assert result == {"last_job_id": 5, "records_added": 0}
