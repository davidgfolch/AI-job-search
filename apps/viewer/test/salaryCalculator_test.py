from decimal import Decimal

from viewer.util.salaryCalculator import calculateYearTax, getYearTaxEquation, getTaxPercentageSpain


def test_calculate_year_tax_under_first_bracket():
    # 10,000 taxed entirely at first bracket (0.19)
    gross = Decimal('10000')
    tax = calculateYearTax(gross)
    assert tax == Decimal('1900')


def test_calculate_year_tax_across_brackets():
    # 20,000: 12,450 at 0.19 and 7,550 at 0.24
    gross = Decimal('20000')
    tax = calculateYearTax(gross)
    # 12450 * 0.19 = 2365.5
    # 7550 * 0.24 = 1812.0
    assert tax == Decimal('2365.5') + Decimal('1812.0')


def test_get_year_tax_equation_represents_terms():
    gross = Decimal('20000')
    eq = getYearTaxEquation(gross)
    # Should contain two terms corresponding to the two taxed brackets
    assert '2365.50' in eq or '12450' in eq
    assert '*' in eq and '+' in eq


def test_get_tax_percentage_spain():
    # 10k -> first bracket percentage (0.19)
    assert getTaxPercentageSpain(Decimal('10000')) == Decimal('0.19')
    # 15k -> second bracket (0.24)
    assert getTaxPercentageSpain(Decimal('15000')) == Decimal('0.24')
    # 100k -> falls in 300000 bracket (0.45)
    assert getTaxPercentageSpain(Decimal('100000')) == Decimal('0.45')
