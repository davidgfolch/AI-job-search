from fastapi import APIRouter, Depends
from typing import List, Dict, Any, Optional
from services.statistics_service import StatisticsService
from services.statistics_archived_service import StatisticsArchivedService

router = APIRouter()
service = StatisticsService()
archived_service = StatisticsArchivedService()


@router.get("/history")
def get_history_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_old_jobs: bool = True,
):
    if include_old_jobs:
        return archived_service.get_combined_history_stats(start_date=start_date, end_date=end_date)
    return service.get_history_stats(start_date=start_date, end_date=end_date)


@router.get("/sources-date")
def get_sources_by_date(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_old_jobs: bool = True,
):
    if include_old_jobs:
        return archived_service.get_combined_sources_by_date(start_date=start_date, end_date=end_date)
    return service.get_sources_by_date(start_date=start_date, end_date=end_date)


@router.get("/sources-hour")
def get_sources_by_hour(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_old_jobs: bool = True,
):
    if include_old_jobs:
        return archived_service.get_combined_sources_by_hour(start_date=start_date, end_date=end_date)
    return service.get_sources_by_hour(start_date=start_date, end_date=end_date)


@router.get("/sources-weekday")
def get_sources_by_weekday(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_old_jobs: bool = True,
):
    if include_old_jobs:
        return archived_service.get_combined_sources_by_weekday(start_date=start_date, end_date=end_date)
    return service.get_sources_by_weekday(start_date=start_date, end_date=end_date)


@router.get("/filter-configs")
def get_filter_config_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_old_jobs: bool = True,
):
    return service.get_filter_configuration_stats(start_date=start_date, end_date=end_date)
