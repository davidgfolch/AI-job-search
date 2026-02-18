from fastapi import APIRouter, Depends
from typing import Optional
from services.statistics_archived_service import StatisticsArchivedService

router = APIRouter()
service = StatisticsArchivedService()


@router.get("/history")
def get_archived_history_stats(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_archived_history_stats(start_date=start_date, end_date=end_date)


@router.get("/sources-date")
def get_archived_sources_by_date(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_archived_sources_by_date(
        start_date=start_date, end_date=end_date
    )


@router.get("/sources-hour")
def get_archived_sources_by_hour(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_archived_sources_by_hour(
        start_date=start_date, end_date=end_date
    )


@router.get("/sources-weekday")
def get_archived_sources_by_weekday(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_archived_sources_by_weekday(
        start_date=start_date, end_date=end_date
    )


@router.get("/combined/history")
def get_combined_history_stats(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_combined_history_stats(start_date=start_date, end_date=end_date)


@router.get("/combined/sources-date")
def get_combined_sources_by_date(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_combined_sources_by_date(
        start_date=start_date, end_date=end_date
    )


@router.get("/combined/sources-hour")
def get_combined_sources_by_hour(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_combined_sources_by_hour(
        start_date=start_date, end_date=end_date
    )


@router.get("/combined/sources-weekday")
def get_combined_sources_by_weekday(
    start_date: Optional[str] = None, end_date: Optional[str] = None
):
    return service.get_combined_sources_by_weekday(
        start_date=start_date, end_date=end_date
    )


@router.get("/snapshots-by-reason")
def get_snapshots_by_reason():
    return service.get_snapshots_by_reason()


@router.get("/snapshots-by-platform")
def get_snapshots_by_platform():
    return service.get_snapshots_by_platform()
