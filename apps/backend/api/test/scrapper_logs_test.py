from unittest.mock import patch


@patch("services.scrapper_logs_service.ScrapperLogsService.append", return_value=2)
def test_ingest_scrapper_logs(mock_append, client):
    records = [{"event": "indeed.results_found"}, {"event": "scraper.job.already_exists"}]
    response = client.post("/api/scrapper/logs", json={"app": "scrapper", "records": records})
    assert response.status_code == 200
    assert response.json() == {"accepted": 2}
    mock_append.assert_called_once_with(records)


def test_rejects_foreign_app(client):
    response = client.post("/api/scrapper/logs", json={"app": "backend", "records": []})
    assert response.status_code == 400
    assert response.json()["detail"] == "Only scrapper logs are accepted"


def test_rejects_oversized_batch(client):
    response = client.post("/api/scrapper/logs", json={"records": [{"event": "x"}] * 1001})
    assert response.status_code == 422
