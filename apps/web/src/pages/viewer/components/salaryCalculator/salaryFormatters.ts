export type CalcMode = 'classic' | 'hoursPerWeek' | 'daysPerMonth';

export interface SalaryCalculatorParams {
    calcMode: CalcMode;
    calcRate: number;
    calcRateType: 'Hourly' | 'Daily';
    calcFreelanceRate: number;
    calcHoursPerWeek: number;
    calcDaysPerMonth: number;
}

const SALARY_DATA_MARKER = '<!-- SALARY_CALC_DATA:';
const SALARY_DATA_END = ' -->';

const paramsEqual = (a: SalaryCalculatorParams, b: SalaryCalculatorParams): boolean => {
    return a.calcMode === b.calcMode &&
        a.calcRate === b.calcRate &&
        a.calcRateType === b.calcRateType &&
        a.calcFreelanceRate === b.calcFreelanceRate &&
        a.calcHoursPerWeek === b.calcHoursPerWeek &&
        a.calcDaysPerMonth === b.calcDaysPerMonth;
};

export const updateCommentsWithSalaryCalc = (comments: string, newParams: SalaryCalculatorParams): string => {
    const newData = `${SALARY_DATA_MARKER}${JSON.stringify(newParams)}${SALARY_DATA_END}`;
    // Find all existing salary calc data
    const dataRegex = /<!-- SALARY_CALC_DATA:(.+?) -->/g;
    const matches = [...comments.matchAll(dataRegex)];
    if (matches.length === 0) {
        // No existing data, just append
        return comments + newData;
    }
    // Check if newParams already exists in any match
    for (const match of matches) {
        try {
            const existingParams = JSON.parse(match[1]) as SalaryCalculatorParams;
            if (paramsEqual(existingParams, newParams)) {
                // Already exists, no change needed
                return comments;
            }
        } catch {
            // Skip invalid JSON
        }
    }
    
    // New params don't exist yet, insert after first occurrence
    let inserted = false;
    return comments.replace(dataRegex, (match) => {
        if (!inserted) {
            inserted = true;
            return match + newData;
        }
        return match;
    });
};

export const parseSalaryCalculationFromComments = (comments: string | null | undefined): SalaryCalculatorParams | null => {
    const all = parseAllSalaryCalculationsFromComments(comments);
    return all.length > 0 ? all[0] : null;
};

export const parseAllSalaryCalculationsFromComments = (comments: string | null | undefined): SalaryCalculatorParams[] => {
    if (!comments) return [];
    const dataRegex = /<!-- SALARY_CALC_DATA:(.+?) -->/g;
    const results: SalaryCalculatorParams[] = [];
    for (const match of comments.matchAll(dataRegex)) {
        try {
            results.push(JSON.parse(match[1]) as SalaryCalculatorParams);
        } catch { /* skip invalid */ }
    }
    return results;
};
