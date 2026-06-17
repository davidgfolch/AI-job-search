from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST
from commonlib.services.metrics_collector import MetricsCollector
from commonlib.prometheus_exporter import build_prometheus_metrics, build_log_metrics

router = APIRouter(tags=["metrics"])

@router.get("/metrics")
def get_prometheus_metrics():
    collector = MetricsCollector()
    collector.reload()
    snapshot = collector.get_snapshot()
    data = build_prometheus_metrics(snapshot)
    log_data = build_log_metrics()
    return Response(content=data + b"\n" + log_data, media_type=CONTENT_TYPE_LATEST)
