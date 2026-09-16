def request_jobs(client, query_params):
    response = client.get(f"/api/jobs?{query_params}")
    assert response.status_code == 200
    return response


def get_query_from_mock(mock_db):
    queries = [str(call[0][0]) for call in mock_db.fetchAll.call_args_list]
    return next((q for q in queries if "SELECT" in q and "FROM" in q), "")


def mock_job_dict(job_id=1):
    return {
        "id": job_id,
        "title": "Job 1",
        "company": "Acme",
        "created": "2023-01-01T00:00:00",
        "modified": "2023-01-01T00:00:00",
    }