from fastapi import APIRouter, HTTPException, Depends
from typing import List
from services.filter_configurations_service import FilterConfigurationsService
from models.filter_configuration import FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate

router = APIRouter()

def get_service():
    return FilterConfigurationsService()

@router.get("", response_model=List[FilterConfiguration])
def get_all_configurations(service: FilterConfigurationsService = Depends(get_service)):
    return service.get_all()

@router.post("", response_model=FilterConfiguration, status_code=201)
def create_configuration(config: FilterConfigurationCreate, service: FilterConfigurationsService = Depends(get_service)):
    try:
        return service.create(config.name, config.filters, config.notify)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{config_id}", response_model=FilterConfiguration)
def get_configuration(config_id: int, service: FilterConfigurationsService = Depends(get_service)):
    try:
        return service.get_by_id(config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{config_id}", response_model=FilterConfiguration)
def update_configuration(config_id: int, config: FilterConfigurationUpdate, service: FilterConfigurationsService = Depends(get_service)):
    try:
        return service.update(config_id, config.name, config.filters, config.notify)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{config_id}", status_code=204)
def delete_configuration(config_id: int, service: FilterConfigurationsService = Depends(get_service)):
    try:
        service.delete(config_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
