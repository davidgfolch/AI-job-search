from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from services.statistics_service import StatisticsService

router = APIRouter()
service = StatisticsService()

@router.get("/history")
def get_history_stats():
    return service.get_history_stats()

@router.get("/sources-date")
def get_sources_by_date():
    return service.get_sources_by_date()

@router.get("/sources-hour")
def get_sources_by_hour():
    return service.get_sources_by_hour()

@router.get("/sources-weekday")
def get_sources_by_weekday():
    return service.get_sources_by_weekday()

@router.get("/filter-configs")
def get_filter_config_stats():
    return service.get_filter_configuration_stats()
