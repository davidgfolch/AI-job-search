from decimal import Decimal
from commonlib.salary import SalaryCalculator

def test_salary_calculation_hourly():
    # Test hourly calculation
    # Rate: 40, Hours: 8, Type: Hourly, Freelance: 80
    # Gross: 40 * 8 * 23.3 * 11 = 82016
    # Tax: Should be calculated based on tramos
    # Net: Gross - Tax - (80 * 12)
    
    rate = Decimal('40')
    hours = Decimal('8')
    freelance = Decimal('80')
    
    result = SalaryCalculator.calculate_salary(rate, 'Hourly', hours, freelance)
    
    assert 'gross_year' in result
    assert 'net_year' in result
    assert result['parsed_equation'] == '40 * 8 * 23.3 * 11'
    
    gross = Decimal(result['gross_year'])
    assert gross > 0

def test_salary_calculation_daily():
    # Test daily calculation
    # Rate: 300, Type: Daily
    # Gross: 300 * 23.3 * 11 = 76890
    
    rate = Decimal('300')
    hours = Decimal('8') # Ignored for daily
    freelance = Decimal('80')
    
    result = SalaryCalculator.calculate_salary(rate, 'Daily', hours, freelance)
    
    assert 'gross_year' in result
    assert result['parsed_equation'] == '300 * 23.3 * 11'
    
    gross = Decimal(result['gross_year'])
    assert gross > 0

def test_tax_brackets():
    # Test tax calculation for specific amount
    gross = Decimal('20000')
    # 0-12450 @ 19% + 12450-20000 @ 24%
    # 12450 * 0.19 = 2365.5
    # (20000 - 12450) * 0.24 = 7550 * 0.24 = 1812
    # Total = 4177.5
    
    tax = SalaryCalculator.calculate_year_tax(gross)
    assert 4170 <= tax <= 4185 # Allow some floating point wiggle room if any, though Decimal handles it well
