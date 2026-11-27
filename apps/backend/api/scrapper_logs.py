from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.scrapper_logs_service import ScrapperLogsService

router = APIRouter()
service = ScrapperLogsService()
MAX_BATCH = 1000


class ScrapperLogBatch(BaseModel):
    app: str = "scrapper"
    records: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_BATCH)


@router.post("/logs")
def ingest_scrapper_logs(batch: ScrapperLogBatch):
    """Receive a batch of JSONL records from a scrapper running on another machine."""
    try:
        service.validate_app(batch.app)
        accepted = service.append(batch.records)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"accepted": accepted}
