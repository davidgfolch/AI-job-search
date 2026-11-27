from typing import Optional
from fastapi import APIRouter, HTTPException
from services.keyword_stats_service import KeywordStatsService

router = APIRouter()
service = KeywordStatsService()


@router.get("/keywords")
def get_keyword_stats(start_date: Optional[str] = None, end_date: Optional[str] = None, site: Optional[str] = None, keyword: Optional[str] = None):
    try:
        return service.get_keyword_stats(start_date=start_date, end_date=end_date, site=site, keyword=keyword)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
