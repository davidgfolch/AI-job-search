import pytest
from decimal import Decimal
from commonlib.salary import SalaryCalculator


@pytest.mark.parametrize(
    "rate,type_name,hours,freelance,expected_equation",
    [
        (Decimal("40"), "Hourly", Decimal("8"), Decimal("80"), "40 * 8 * 23.3 * 11"),
        (Decimal("300"), "Daily", Decimal("8"), Decimal("80"), "300 * 23.3 * 11"),
    ],
)
def test_salary_calculations(rate, type_name, hours, freelance, expected_equation):
    result = SalaryCalculator.calculate_salary(rate, type_name, hours, freelance)
    assert "gross_year" in result
    assert "net_year" in result
    assert result["parsed_equation"] == expected_equation
    gross = Decimal(result["gross_year"])
    assert gross > 0


def test_salary_calculation_daily():
    rate = Decimal("300")
    hours = Decimal("8")
    freelance = Decimal("80")
    result = SalaryCalculator.calculate_salary(rate, "Daily", hours, freelance)
    assert result["parsed_equation"] == "300 * 23.3 * 11"
    gross = Decimal(result["gross_year"])
    assert gross > 0


def test_tax_brackets():
    gross = Decimal("20000")
    tax = SalaryCalculator.calculate_year_tax(gross)
    assert 4170 <= tax <= 4185


def test_tax_bracket_zero():
    tax = SalaryCalculator.calculate_year_tax(Decimal("0"))
    assert tax == Decimal("0")


def test_tax_bracket_below_first():
    tax = SalaryCalculator.calculate_year_tax(Decimal("5000"))
    assert tax > 0


def test_tax_bracket_all_brackets():
    tax = SalaryCalculator.calculate_year_tax(Decimal("300000"))
    assert tax > 0


def test_get_year_tax_equation():
    eq = SalaryCalculator.get_year_tax_equation(Decimal("20000"))
    assert "(" in eq
    assert "*" in eq


def test_get_year_tax_equation_zero():
    eq = SalaryCalculator.get_year_tax_equation(Decimal("0"))
    assert eq == "0"


def test_calculate_salary_hourly():
    result = SalaryCalculator.calculate_salary(Decimal("50"), "Hourly", Decimal("8"), Decimal("100"))
    assert Decimal(result["gross_year"]) > 0
    assert Decimal(result["net_month"]) > 0
    assert "gross_year" in result
    assert "net_year" in result
    assert "year_tax" in result
    assert "freelance_tax" in result
