import { describe, it, expect } from 'vitest';
import { formatCalculationForComments } from '../salaryFormatters';

describe('salaryFormatters', () => {
    it('formats calculation', () => {
        const result = formatCalculationForComments({
            result: { gross_year: 10000, year_tax: 2000, net_year: 8000, net_month: 666, parsed_equation: 'eq' } as any,
            calcMode: 'classic',
            calcRate: 100,
            calcRateType: 'Hourly',
            calcFreelanceRate: 150,
            calcHoursPerWeek: 40,
            calcDaysPerMonth: 20
        });
        expect(result).toContain('Salary Calculation');
        expect(result).toContain('Gross/year: 10000');
    });
});
