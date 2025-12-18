import streamlit as st
from decimal import Decimal
from viewer.util.stUtil import inColumns
from viewer.util.stStateUtil import getState
from commonlib.salary import SalaryCalculator

def calculator():
    rate = Decimal(getState('calculatorRate', 40))
    hours_x_day = Decimal(getState('calculatorHoursXDay', 8))
    rate_type = getState('calculatorRateType', 'Hourly')
    freelance_rate = Decimal(getState("calculatorFreelanceRate", 80))

    result = SalaryCalculator.calculate_salary(rate, rate_type, hours_x_day, freelance_rate)

    grossYear = result['gross_year']
    parsedEquation = result['parsed_equation']
    yearTax = result['year_tax']
    yearTaxEquation = result['year_tax_equation']
    netYear = result['net_year']
    netMonth = result['net_month']
    freelanceTax = result['freelance_tax']
    grossYearVal = Decimal(grossYear)

    inColumns([(1, lambda _: st.number_input('Rate', key='calculatorRate')),
               (1, lambda _: st.selectbox('Rate type', ('Hourly', 'Daily'), key='calculatorRateType')),
               (1, lambda _: st.selectbox('Freelance month rate', ('80', '300'), key='calculatorFreelanceRate')),
               (2, lambda _: st.markdown('<span style="font-family:monospace;">' +
                                         f'Gr/ year: :green[{grossYear}]   <span style="font-size: small">({parsedEquation})</span>  \n' +
                                         f'Tax year: :green[{yearTax}]   <span style="font-size: small">({yearTaxEquation})</span>  \n' +
                                         f'Net year: :green[{netYear}] <span style="font-size: small">({grossYear} - {yearTax} - {freelanceTax})</span>   \n' +
                                         f'Net motn: :green[{netMonth}]' +
                                         '</span>', unsafe_allow_html=True)),
               ])
