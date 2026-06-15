from fastapi import APIRouter
from commonlib.services.metrics_collector import MetricsCollector

router = APIRouter(tags=["metrics"])

@router.get("/enrichment/metrics")
def get_enrichment_metrics():
    collector = MetricsCollector()
    snapshot = collector.get_snapshot()
    if not snapshot.get("modules"):
        return {"status": "no_data", "message": "No enrichment jobs have been processed yet."}
    return {"status": "ok", "data": snapshot}
