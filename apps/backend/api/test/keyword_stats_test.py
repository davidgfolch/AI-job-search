from unittest.mock import patch


@patch('services.keyword_stats_service.KeywordStatsService.get_keyword_stats')
def test_get_keyword_stats(mock_stats, client):
    payload = {"items": [{"date": "2026-11-19", "site": "Indeed", "keyword": "python", "duplicates": 2}], "truncated": False}
    mock_stats.return_value = payload
    response = client.get("/api/statistics/keywords?site=Indeed&keyword=python")
    assert response.status_code == 200
    assert response.json() == payload
    mock_stats.assert_called_once_with(start_date=None, end_date=None, site="Indeed", keyword="python")


@patch('services.keyword_stats_service.KeywordStatsService.get_keyword_stats', side_effect=ValueError("bad date"))
def test_get_keyword_stats_rejects_invalid_date(mock_stats, client):
    response = client.get("/api/statistics/keywords?start_date=nope")
    assert response.status_code == 400
    assert response.json()["detail"] == "bad date"
