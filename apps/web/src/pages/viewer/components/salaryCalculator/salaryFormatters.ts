import type { SalaryCalculationResponse } from '../api/salary';

type CalcMode = 'classic' | 'hoursPerWeek' | 'daysPerMonth';

interface FormatParams {
    result: SalaryCalculationResponse;
    calcMode: CalcMode;
    calcRate: number;
    calcRateType: 'Hourly' | 'Daily';
    calcFreelanceRate: number;
    calcHoursPerWeek: number;
    calcDaysPerMonth: number;
}

export const formatCalculationForComments = (params: FormatParams): string => {
    const { result, calcMode, calcRate, calcRateType, calcFreelanceRate, calcHoursPerWeek, calcDaysPerMonth } = params;
    const timestamp = new Date().toLocaleString();
    let modeInfo = '';
    if (calcMode === 'classic') {
        modeInfo = `Mode: Classic | Rate: **${calcRate}** (${calcRateType})`;
    } else if (calcMode === 'hoursPerWeek') {
        modeInfo = `Mode: Hours/Week | Rate: **${calcRate}**/hr | Hours/Week: **${calcHoursPerWeek}**`;
    } else {
        modeInfo = `Mode: Days/Month | Rate: **${calcRate}**/day | Days/Month: **${calcDaysPerMonth}**`;
    }
    return `\n---\n**Salary Calculation** (${timestamp})\n${modeInfo} | Freelance: ${calcFreelanceRate}\n- Gross/year: ${result.gross_year} (${result.parsed_equation})\n- Tax/year: ${result.year_tax}\n- Net/year: ${result.net_year}\n- Net/month: **${result.net_month}**\n`;
};

export const removePreviousSalaryCalculation = (comments: string): string => {
    // Remove any existing salary calculation block
    // Pattern: from "---" + newline + "**Salary Calculation**" through the final newline of the block
    // The block ends with "- Net/month: XXXXX\n"
    const salaryCalcRegex = /\n---\n\*\*Salary Calculation\*\*[^\n]*\n(?:.*\n)*?- Net\/month: [^\n]*\n/g;
    return comments.replace(salaryCalcRegex, '');
};
