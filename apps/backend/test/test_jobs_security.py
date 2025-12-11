import pytest


def test_get_applied_jobs_by_company_sql_injection_semicolon(client):
    """Test that SQL injection with semicolon is blocked"""
    response = client.get("/api/jobs/applied-by-company?company=Company;%20DROP%20TABLE%20jobs")
    assert response.status_code == 400
    assert "semicolon" in response.json()['detail'].lower()


def test_get_applied_jobs_by_company_sql_injection_union(client):
    """Test that SQL injection with UNION is blocked"""
    response = client.get("/api/jobs/applied-by-company?company=Company%20UNION%20SELECT")
    assert response.status_code == 400
    assert "union" in response.json()['detail'].lower()


def test_get_applied_jobs_by_company_sql_injection_select(client):
    """Test that SQL injection with SELECT is blocked"""
    response = client.get("/api/jobs/applied-by-company?company=SELECT%20*%20FROM%20jobs")
    assert response.status_code == 400
    assert "select" in response.json()['detail'].lower()


def test_get_applied_jobs_by_company_sql_injection_in_client(client):
    """Test that SQL injection in client parameter is blocked"""
    response = client.get("/api/jobs/applied-by-company?company=joppy&client=Client;%20DROP%20TABLE")
    assert response.status_code == 400
    assert "semicolon" in response.json()['detail'].lower()


def test_get_applied_jobs_by_company_missing_parameter(client):
    """Test that missing company parameter returns validation error"""
    response = client.get("/api/jobs/applied-by-company")
    assert response.status_code == 422

def test_get_applied_jobs_by_company_empty_string(client):
    """Test that empty company parameter is rejected"""
    response = client.get("/api/jobs/applied-by-company?company=")
    assert response.status_code == 400
    assert "must be a non-empty string" in response.json()['detail']
