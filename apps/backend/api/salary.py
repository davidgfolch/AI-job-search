from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal
from typing import Dict, Optional
from commonlib.observability import get_logger
from services.salary_service import SalaryService

logger = get_logger("backend.api.salary")

router = APIRouter()

class SalaryCalculationRequest(BaseModel):
    rate: float
    rate_type: str = 'Hourly'
    hours_x_day: float = 8.0
    freelance_rate: float = 80.0

@router.post("/calculate")
async def calculate_salary(request: SalaryCalculationRequest):
    try:
        # Convert floats to Decimals for precision in calculation
        rate = Decimal(str(request.rate))
        hours_x_day = Decimal(str(request.hours_x_day))
        freelance_rate = Decimal(str(request.freelance_rate))
        
        result = SalaryService.calculate_salary(
            rate=rate,
            rate_type=request.rate_type,
            hours_x_day=hours_x_day,
            freelance_rate=freelance_rate
        )
        return result
    except Exception as e:
        logger.exception("salary.calculation_failed", error=str(e), rate_type=request.rate_type)
        raise HTTPException(status_code=500, detail=str(e))
