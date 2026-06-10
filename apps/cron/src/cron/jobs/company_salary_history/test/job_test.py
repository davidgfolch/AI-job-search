from cron.jobs.company_salary_history.job import CompanySalaryHistoryJob


def test_job_has_name_and_cadency():
    job = CompanySalaryHistoryJob(cadency="1h")
    assert job.name == "companySalaryHistory"
    assert job.cadency == "1h"
