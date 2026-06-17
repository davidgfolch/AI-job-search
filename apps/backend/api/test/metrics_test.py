from unittest.mock import patch, MagicMock
from prometheus_client import CONTENT_TYPE_LATEST


def test_get_prometheus_metrics(client):
    mock_collector = MagicMock()
    mock_collector.get_snapshot.return_value = {"job_count": 5}
    mock_prom_data = b"# HELP job_count Total jobs\n# TYPE job_count gauge\njob_count 5"
    mock_log_data = b"# HELP log_errors Total errors\n# TYPE log_errors gauge\nlog_errors 0"

    with patch("api.metrics.MetricsCollector", return_value=mock_collector):
        with patch("api.metrics.build_prometheus_metrics", return_value=mock_prom_data):
            with patch("api.metrics.build_log_metrics", return_value=mock_log_data):
                response = client.get("/api/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    assert response.content == mock_prom_data + b"\n" + mock_log_data
