from cron.jobs.company_salary_history.scanner import CompanySalaryHistoryScanner


def test_scanner_imports():
    assert CompanySalaryHistoryScanner is not None
