from fastapi import APIRouter, HTTPException, Depends
from typing import List
from commonlib.observability import get_logger
from services.filter_configurations_service import FilterConfigurationsService
from models.filter_configuration import FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate

logger = get_logger("backend.api.filter_configurations")

router = APIRouter()

def get_service():
    return FilterConfigurationsService()

@router.get("", response_model=List[FilterConfiguration])
def get_all_configurations(service: FilterConfigurationsService = Depends(get_service)):
    return service.get_all()

@router.post("", response_model=FilterConfiguration, status_code=201)
def create_configuration(config: FilterConfigurationCreate, service: FilterConfigurationsService = Depends(get_service)):
    try:
        return service.create(config.name, config.filters, config.watched, config.statistics, config.pinned, config.ordering)
    except ValueError as e:
        logger.warning("api.request_rejected", operation="create", status_code=400, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{config_id}", response_model=FilterConfiguration)
def get_configuration(config_id: int, service: FilterConfigurationsService = Depends(get_service)):
    try:
        return service.get_by_id(config_id)
    except ValueError as e:
        logger.warning("api.request_rejected", operation="get", status_code=404, config_id=config_id, error=str(e))
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{config_id}", response_model=FilterConfiguration)
def update_configuration(config_id: int, config: FilterConfigurationUpdate, service: FilterConfigurationsService = Depends(get_service)):
    try:
        return service.update(config_id, config.name, config.filters, config.watched, config.statistics, config.pinned, config.ordering)
    except ValueError as e:
        logger.warning("api.request_rejected", operation="update", status_code=400, config_id=config_id, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{config_id}", status_code=204)
def delete_configuration(config_id: int, service: FilterConfigurationsService = Depends(get_service)):
    try:
        service.delete(config_id)
    except ValueError as e:
        logger.warning("api.request_rejected", operation="delete", status_code=404, config_id=config_id, error=str(e))
        raise HTTPException(status_code=404, detail=str(e))
