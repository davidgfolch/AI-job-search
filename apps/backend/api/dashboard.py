from fastapi import APIRouter
from services import dashboard_service as service

router = APIRouter(tags=["dashboard"])


@router.get("/services")
def get_services_status():
    return service.get_services_status()
