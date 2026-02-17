import { describe, it, expect } from 'vitest';
import { updateCommentsWithSalaryCalc, parseSalaryCalculationFromComments, parseAllSalaryCalculationsFromComments, type SalaryCalculatorParams } from '../salaryFormatters';

const baseParams: SalaryCalculatorParams = {
    calcMode: 'classic',
    calcRate: 50,
    calcRateType: 'Hourly',
    calcFreelanceRate: 80,
    calcHoursPerWeek: 40,
    calcDaysPerMonth: 20,
};

describe('updateCommentsWithSalaryCalc', () => {
    it('should append params to empty comments', () => {
        const result = updateCommentsWithSalaryCalc('', baseParams);
        expect(result).toContain('SALARY_CALC_DATA');
        expect(result).toContain('"calcRate":50');
    });

    it('should append params to existing comments without salary data', () => {
        const result = updateCommentsWithSalaryCalc('Some notes', baseParams);
        expect(result).toContain('Some notes');
        expect(result).toContain('SALARY_CALC_DATA');
    });

    it('should not duplicate when saving same params', () => {
        const existingData = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const result = updateCommentsWithSalaryCalc(existingData, baseParams);
        const matches = result.match(/SALARY_CALC_DATA/g);
        expect(matches).toHaveLength(1);
    });

    it('should append different params after first one', () => {
        const existingData = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const newParams = { ...baseParams, calcRate: 100 };
        const result = updateCommentsWithSalaryCalc(existingData, newParams);
        const matches = result.match(/SALARY_CALC_DATA/g);
        expect(matches).toHaveLength(2);
        expect(result).toContain('"calcRate":50');
        expect(result).toContain('"calcRate":100');
    });

    it('should not add duplicate when params already exist among multiple', () => {
        const existingData = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} --><!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":100,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const newParams = { ...baseParams, calcRate: 100 };
        const result = updateCommentsWithSalaryCalc(existingData, newParams);
        const matches = result.match(/SALARY_CALC_DATA/g);
        expect(matches).toHaveLength(2);
    });

});

describe('parseSalaryCalculationFromComments', () => {
    it('should return null for empty comments', () => {
        expect(parseSalaryCalculationFromComments('')).toBeNull();
        expect(parseSalaryCalculationFromComments(null)).toBeNull();
        expect(parseSalaryCalculationFromComments(undefined)).toBeNull();
    });

    it('should return null for comments without salary data', () => {
        expect(parseSalaryCalculationFromComments('Some random notes')).toBeNull();
    });

    it('should parse valid salary data from comments', () => {
        const comments = 'Notes <!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} --> more';
        const result = parseSalaryCalculationFromComments(comments);
        expect(result).toEqual({
            calcMode: 'classic',
            calcRate: 50,
            calcRateType: 'Hourly',
            calcFreelanceRate: 80,
            calcHoursPerWeek: 40,
            calcDaysPerMonth: 20,
        });
    });

    it('should return first params when multiple exist', () => {
        const comments = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} --><!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":100,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const result = parseSalaryCalculationFromComments(comments);
        expect(result?.calcRate).toBe(50);
    });

    it('should return null for invalid JSON', () => {
        const comments = '<!-- SALARY_CALC_DATA:invalid json -->';
        expect(parseSalaryCalculationFromComments(comments)).toBeNull();
    });
});

describe('parseAllSalaryCalculationsFromComments', () => {
    it.each([
        ['empty string', '', 0],
        ['null', null, 0],
        ['undefined', undefined, 0],
        ['no salary data', 'Some random notes', 0],
    ])('should return empty array for %s', (_, comments, expected) => {
        expect(parseAllSalaryCalculationsFromComments(comments as any)).toHaveLength(expected);
    });

    it('should parse single salary data', () => {
        const comments = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const result = parseAllSalaryCalculationsFromComments(comments);
        expect(result).toHaveLength(1);
        expect(result[0].calcRate).toBe(50);
    });

    it('should parse multiple salary data entries', () => {
        const comments = '<!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} --><!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":100,"calcRateType":"Daily","calcFreelanceRate":300,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const result = parseAllSalaryCalculationsFromComments(comments);
        expect(result).toHaveLength(2);
        expect(result[0].calcRate).toBe(50);
        expect(result[1].calcRate).toBe(100);
    });

    it('should skip invalid JSON entries', () => {
        const comments = '<!-- SALARY_CALC_DATA:invalid --><!-- SALARY_CALC_DATA:{"calcMode":"classic","calcRate":50,"calcRateType":"Hourly","calcFreelanceRate":80,"calcHoursPerWeek":40,"calcDaysPerMonth":20} -->';
        const result = parseAllSalaryCalculationsFromComments(comments);
        expect(result).toHaveLength(1);
        expect(result[0].calcRate).toBe(50);
    });
});
