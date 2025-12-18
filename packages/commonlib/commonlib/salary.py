from decimal import Decimal
from typing import Dict, Tuple
from mathparse import mathparse

class SalaryCalculator:
    tramos = [
        (Decimal('12450'), Decimal('0.19')),
        (Decimal('20200'), Decimal('0.24')),
        (Decimal('35200'), Decimal('0.30')),
        (Decimal('60000'), Decimal('0.37')),
        (Decimal('300000'), Decimal('0.45')),
        (Decimal('Infinity'), Decimal('0.47'))
    ]

    @staticmethod
    def calculate_year_tax(gross_year: Decimal) -> Decimal:
        """Calculate the actual tax amount"""
        tax = Decimal('0')
        previous_limit = Decimal('0')
        for limit, percentage in SalaryCalculator.tramos:
            if gross_year <= previous_limit:
                break
            taxable_in_bracket = min(gross_year, limit) - previous_limit
            if taxable_in_bracket > 0:
                tax += taxable_in_bracket * percentage
            if gross_year <= limit:
                break
            previous_limit = limit
        return tax

    @staticmethod
    def get_year_tax_equation(gross_year: Decimal) -> str:
        """Generate a string representation of the tax calculation"""
        result = ''
        previous_limit = Decimal('0')
        for limit, percentage in SalaryCalculator.tramos:
            if gross_year <= previous_limit:
                break
            taxable_in_bracket = min(gross_year, limit) - previous_limit
            if taxable_in_bracket > 0:
                result += ('' if result == '' else ' + ')
                result += f'({taxable_in_bracket:.2f} * {percentage:.2f})'
            if gross_year <= limit:
                break
            previous_limit = limit
        return result if result else '0'

    @staticmethod
    def calculate_salary(rate: Decimal, rate_type: str, hours_x_day: Decimal, freelance_rate: Decimal) -> Dict[str, str]:
        equations: Dict[str, str] = {
            'Hourly': '{rate} * {hoursXDay} * 23.3 * 11',
            'Daily': '{rate} * 23.3 * 11',
        }

        if rate_type == 'Hourly':
            gross_year = rate * hours_x_day * Decimal('23.3') * Decimal('11')
        else: # Daily
            gross_year = rate * Decimal('23.3') * Decimal('11')

        parsed_equation = equations.get(rate_type, equations['Hourly']) \
            .format(rate=str(rate), hoursXDay=str(hours_x_day))
            
        # gross_year is already Decimal, no need to parse string
        year_tax_equation = SalaryCalculator.get_year_tax_equation(gross_year)
        year_tax = SalaryCalculator.calculate_year_tax(gross_year)
        freelance_tax = freelance_rate * Decimal('12')
        net_year = gross_year - year_tax - freelance_tax
        net_month = net_year / Decimal('12')

        return {
            'gross_year': f'{gross_year:.2f}',
            'parsed_equation': parsed_equation,
            'year_tax': f'{year_tax:.0f}',
            'year_tax_equation': year_tax_equation,
            'net_year': f'{net_year:.0f}',
            'net_month': f'{net_month:.0f}',
            'freelance_tax': f'{freelance_tax:.0f}'
        }
