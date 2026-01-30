import pytest
from models.job import Job, JobBase, JobCreate, JobUpdate, JobListResponse, AppliedCompanyJob
from datetime import datetime

def test_job_base_creation():
    job = JobBase(title="Developer", company="ACME", location="Madrid")
    assert job.title == "Developer"
    assert job.company == "ACME"
    assert job.location == "Madrid"

@pytest.mark.parametrize("field,value", [
    ("flagged", True), ("like", False), ("ignored", True),
    ("seen", False), ("applied", True), ("discarded", False)
])
def test_job_base_boolean_fields(field, value):
    job = JobBase(**{field: value})
    assert getattr(job, field) == value

def test_job_creation():
    job = Job(id=1, title="Developer", company="ACME", created=datetime.now())
    assert job.id == 1
    assert job.title == "Developer"

def test_job_create_validation():
    job = JobCreate(title="Developer", company="ACME")
    assert job.title == "Developer"
    assert job.company == "ACME"

def test_job_update():
    job = JobUpdate(comments="Good position")
    assert job.comments == "Good position"

def test_job_list_response():
    jobs = [Job(id=1, title="Dev", company="ACME")]
    response = JobListResponse(items=jobs, total=1, page=1, size=20)
    assert response.total == 1
    assert len(response.items) == 1

def test_applied_company_job():
    job = AppliedCompanyJob(id=1, created="2023-01-01")
    assert job.id == 1
    assert job.created == "2023-01-01"
