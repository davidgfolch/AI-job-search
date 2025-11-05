import streamlit as st
from mathparse import mathparse

from decimal import Decimal
from typing import Dict

from viewer.util.stUtil import inColumns
from viewer.util.stStateUtil import getState


def calculator():
    equations: Dict[str, str] = {
        'Hourly': '{rate} * {hoursXDay} * 23.3 * 11',
        'Daily': '{rate} * 23.3 * 11',
    }
    parsedEquation = equations[getState('calculatorRateType', 'Hourly')] \
        .format(rate=Decimal(getState('calculatorRate', 40)),
                hoursXDay=Decimal(getState('calculatorHoursXDay', 8)))
    grossYear = Decimal(mathparse.parse(parsedEquation))
    yearTaxEquation = getYearTaxEquation(grossYear)
    yearTax = calculateYearTax(grossYear)  # Use direct calculation
    freelanceTax = Decimal(getState("calculatorFreelanceRate", 80)) * 12
    netYear = grossYear - yearTax - freelanceTax
    inColumns([(1, lambda _: st.number_input('Rate', key='calculatorRate')),
               (1, lambda _: st.selectbox('Rate type', ('Hourly', 'Daily'), key='calculatorRateType')),
               (1, lambda _: st.selectbox('Freelance month rate', ('80', '300'), key='calculatorFreelanceRate')),
               (2, lambda _: st.markdown('<span style="font-family:monospace;">' +
                                         f'Gr/ year: :green[{grossYear}]   <span style="font-size: small">({parsedEquation})</span>  \n' +
                                         f'Tax year: :green[{yearTax:.0f}]   <span style="font-size: small">({yearTaxEquation})</span>  \n' +
                                         f'Net year: :green[{netYear:.0f}] <span style="font-size: small">({str(grossYear)} - {yearTax:.0f} - {freelanceTax:.0f})</span>   \n' +
                                         f'Net motn: :green[{(netYear/12):.0f}]' +
                                         '</span>', unsafe_allow_html=True)),
               ])


def calculateYearTax(grossYear: Decimal) -> Decimal:
    """Calculate the actual tax amount"""
    tax = Decimal('0')
    previousLimit = Decimal('0')
    for limit, percentage in tramos:
        if grossYear <= previousLimit:
            break
        taxableInBracket = min(grossYear, limit) - previousLimit
        if taxableInBracket > 0:
            tax += taxableInBracket * percentage
        if grossYear <= limit:
            break
        previousLimit = limit
    return tax


tramos = [
    (Decimal('12450'), Decimal('0.19')),
    (Decimal('20200'), Decimal('0.24')),
    (Decimal('35200'), Decimal('0.30')),
    (Decimal('60000'), Decimal('0.37')),
    (Decimal('300000'), Decimal('0.45')),
    (Decimal('Infinity'), Decimal('0.47'))
]


def getYearTaxEquation(grossYear: Decimal) -> str:
    """Generate a string representation of the tax calculation"""
    result = ''
    previousLimit = Decimal('0')
    for limit, percentage in tramos:
        if grossYear <= previousLimit:
            break
        taxableInBracket = min(grossYear, limit) - previousLimit
        if taxableInBracket > 0:
            result += ('' if result == '' else ' + ')
            result += f'({taxableInBracket:.2f} * {percentage:.2f})'
        if grossYear <= limit:
            break
        previousLimit = limit
    return result if result else '0'


def getTaxPercentageSpain(grossSalary) -> Decimal:
    for limit, percentage in tramos:
        if grossSalary <= limit:
            return Decimal(percentage)
    return Decimal(tramos[len(tramos)-1])
