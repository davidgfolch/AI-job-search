import pytest


@pytest.mark.parametrize("query_params, expected_error", [
    ("company=Company;%20DROP%20TABLE%20jobs", "semicolon"),
    ("company=Company%20UNION%20SELECT", "union"),
    ("company=SELECT%20*%20FROM%20jobs", "select"),
    ("company=joppy&client=Client;%20DROP%20TABLE", "semicolon"),
], ids=["semicolon_company", "union", "select", "semicolon_client"])
def test_get_applied_jobs_sql_injection(client, query_params, expected_error):
    """Test that various SQL injection attempts are blocked"""
    response = client.get(f"/api/jobs/applied-by-company?{query_params}")
    assert response.status_code == 400
    assert expected_error in response.json()['detail'].lower()


def test_get_applied_jobs_by_company_missing_parameter(client):
    """Test that missing company parameter returns validation error"""
    response = client.get("/api/jobs/applied-by-company")
    assert response.status_code == 422

def test_get_applied_jobs_by_company_empty_string(client):
    """Test that empty company parameter is rejected"""
    response = client.get("/api/jobs/applied-by-company?company=")
    assert response.status_code == 400
    assert "must be a non-empty string" in response.json()['detail']
