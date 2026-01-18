import pytest
from unittest.mock import patch
from services.salary_service import SalaryService

@patch('services.salary_service.SalaryCalculator.calculate_salary')
def test_calculate_salary(mock_calculate):
    mock_result = {
        "gross_year": 100000,
        "net_year": 70000,
        "parsed_equation": "40 * 8 * 23.3 * 11"
    }
    mock_calculate.return_value = mock_result
    result = SalaryService.calculate_salary(
        rate=40,
        rate_type="Hourly",
        hours_x_day=8,
        freelance_rate=80
    )
    assert result == mock_result
    mock_calculate.assert_called_once_with(
        rate=40,
        rate_type="Hourly",
        hours_x_day=8,
        freelance_rate=80
    )

@pytest.mark.parametrize("rate,rate_type,hours,freelance", [
    (40, "Hourly", 8, 80),
    (300, "Daily", 8, 80),
    (50, "Hourly", 7, 90)
])
@patch('services.salary_service.SalaryCalculator.calculate_salary')
def test_calculate_salary_params(mock_calculate, rate, rate_type, hours, freelance):
    mock_calculate.return_value = {"gross_year": 100000}
    SalaryService.calculate_salary(rate, rate_type, hours, freelance)
    mock_calculate.assert_called_once_with(
        rate=rate,
        rate_type=rate_type,
        hours_x_day=hours,
        freelance_rate=freelance
    )
