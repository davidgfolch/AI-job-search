import { describe, it, expect } from 'vitest';
import { formatCalculationForComments } from '../salaryFormatters';

describe('salaryFormatters', () => {
    describe.each([
        {
            name: 'classic hourly calculation',
            input: {
                result: { gross_year: 10000, year_tax: 2000, net_year: 8000, net_month: 666, parsed_equation: 'eq' } as any,
                calcMode: 'classic' as const,
                calcRate: 100,
                calcRateType: 'Hourly' as const,
                calcFreelanceRate: 150,
                calcHoursPerWeek: 40,
                calcDaysPerMonth: 20
            },
            expectedContains: ['Salary Calculation', 'Gross/year: 10000', 'Net/year: 8000', 'Net/month: 666', 'Tax/year: 2000']
        },
        {
            name: 'classic salary calculation',
            input: {
                result: { gross_year: 50000, year_tax: 12500, net_year: 37500, net_month: 3125, parsed_equation: 'eq' } as any,
                calcMode: 'classic' as const,
                calcRate: 50000,
                calcRateType: 'Yearly' as const,
                calcFreelanceRate: 150,
                calcHoursPerWeek: 40,
                calcDaysPerMonth: 20
            },
            expectedContains: ['Salary Calculation', 'Gross/year: 50000', 'Net/year: 37500', 'Net/month: 3125', 'Tax/year: 12500']
        },
        {
            name: 'freelance calculation',
            input: {
                result: { gross_year: 312000, year_tax: 78000, net_year: 234000, net_month: 19500, parsed_equation: 'eq' } as any,
                calcMode: 'freelance' as const,
                calcRate: 150,
                calcRateType: 'Hourly' as const,
                calcFreelanceRate: 150,
                calcHoursPerWeek: 40,
                calcDaysPerMonth: 20
            },
            expectedContains: ['Salary Calculation', 'Gross/year: 312000', 'Net/year: 234000', 'Net/month: 19500', 'Tax/year: 78000']
        }
    ])('$name', ({ input, expectedContains }) => {
        it('formats calculation with all expected fields', () => {
            const result = formatCalculationForComments(input);
            
            expectedContains.forEach(expectedText => {
                expect(result).toContain(expectedText);
            });
        });
    });

    describe('edge cases', () => {
        it.each([
            {
                name: 'zero values',
                input: {
                    result: { gross_year: 0, year_tax: 0, net_year: 0, net_month: 0, parsed_equation: 'eq' } as any,
                    calcMode: 'classic' as const,
                    calcRate: 0,
                    calcRateType: 'Hourly' as const,
                    calcFreelanceRate: 0,
                    calcHoursPerWeek: 0,
                    calcDaysPerMonth: 0
                }
            },
            {
                name: 'very high values',
                input: {
                    result: { gross_year: 1000000, year_tax: 300000, net_year: 700000, net_month: 58333, parsed_equation: 'eq' } as any,
                    calcMode: 'classic' as const,
                    calcRate: 500,
                    calcRateType: 'Hourly' as const,
                    calcFreelanceRate: 500,
                    calcHoursPerWeek: 40,
                    calcDaysPerMonth: 20
                }
            }
        ])('handles $name', ({ input }) => {
            expect(() => formatCalculationForComments(input)).not.toThrow();
        });
    });
});
