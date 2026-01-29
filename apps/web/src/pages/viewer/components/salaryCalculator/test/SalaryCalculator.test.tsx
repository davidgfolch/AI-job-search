import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import SalaryCalculator from '../SalaryCalculator';
import { salaryApi } from '../../../api/ViewerSalaryApi';
import { mockSalaryResponse, waitForDebounce, skipInitialCalculation, mockJob } from './SalaryCalculatorTestHelpers';

vi.mock('../../../api/ViewerSalaryApi', () => ({
    salaryApi: {
        calculate: vi.fn(),
    },
}));

describe('SalaryCalculator', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('should render initial inputs', () => {
        render(<SalaryCalculator />);
        expect(screen.getByText('Salary Calculator')).toBeInTheDocument();
        expect(screen.getByRole('spinbutton')).toHaveValue(40);
        expect(screen.getByDisplayValue('Hourly')).toBeInTheDocument();
        expect(screen.getByDisplayValue('80')).toBeInTheDocument();
    });

    it('should call calculate API after debounce when inputs change', async () => {
        (salaryApi.calculate as any).mockResolvedValue(mockSalaryResponse({ gross_year: '1000' }));
        render(<SalaryCalculator />);

        const rateInput = screen.getByRole('spinbutton');
        fireEvent.change(rateInput, { target: { value: '50' } });

        expect(salaryApi.calculate).not.toHaveBeenCalled();
        await waitForDebounce();

        expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining({ rate: 50 }));
        expect(screen.getByText('1000')).toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        (salaryApi.calculate as any).mockRejectedValue(new Error('API Error'));

        render(<SalaryCalculator />);
        skipInitialCalculation();
        (salaryApi.calculate as any).mockClear();

        fireEvent.change(screen.getByRole('spinbutton'), { target: { value: '60' } });
        await waitForDebounce();

        expect(salaryApi.calculate).toHaveBeenCalled();
        expect(consoleSpy).toHaveBeenCalledWith('Error calculating salary:', expect.any(Error));
        consoleSpy.mockRestore();
    });

    it('should update other inputs correctly', async () => {
        (salaryApi.calculate as any).mockResolvedValue(mockSalaryResponse({ gross_year: '9999' }));
        render(<SalaryCalculator />);
        
        skipInitialCalculation();
        (salaryApi.calculate as any).mockClear();

        const selects = screen.getAllByRole('combobox');
        fireEvent.change(selects[1], { target: { value: 'Daily' } });
        fireEvent.change(selects[2], { target: { value: '300' } });

        await waitForDebounce();

        expect(screen.getByText('9999')).toBeInTheDocument();
        expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining({
            rate_type: 'Daily',
            freelance_rate: 300,
        }));
    });

    describe.each([
        ['hoursPerWeek', 'Hours/Week', 'Hourly Rate:', 'Hours/Week:', 1, '20', { rate_type: 'Hourly', hours_x_day: 4 }],
        ['daysPerMonth', 'Days/Month', 'Daily Rate:', 'Days/Month:', 1, '10', { rate_type: 'Daily', rate: expect.closeTo(42.92, 0.1) }],
    ])('Calculation mode: %s', (mode, modeLabel, label1, label2, inputIndex, inputValue, expectedCall) => {
        it(`should calculate correctly in ${modeLabel} mode`, async () => {
            (salaryApi.calculate as any).mockResolvedValue(mockSalaryResponse());
            render(<SalaryCalculator />);
            
            skipInitialCalculation();
            (salaryApi.calculate as any).mockClear();

            fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: mode } });

            expect(screen.getByText(label1)).toBeInTheDocument();
            expect(screen.getByText(label2)).toBeInTheDocument();

            const inputs = screen.getAllByRole('spinbutton');
            if (mode === 'daysPerMonth') {
                fireEvent.change(inputs[0], { target: { value: '100' } });
            }
            fireEvent.change(inputs[inputIndex], { target: { value: inputValue } });

            await waitForDebounce();
            expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining(expectedCall));
        });
    });

    it('should save calculation to job comments when Save button is clicked', async () => {
        const mockOnUpdate = vi.fn();
        (salaryApi.calculate as any).mockResolvedValue(mockSalaryResponse({
            gross_year: '88000.00',
            parsed_equation: '40 * 8 * 23.3 * 11',
            year_tax: '15000',
            net_year: '70000',
            net_month: '5833',
        }));

        render(<SalaryCalculator job={mockJob as any} onUpdate={mockOnUpdate} />);
        await waitForDebounce();

        expect(mockOnUpdate).not.toHaveBeenCalled();

        fireEvent.click(screen.getByText('💾 Save to Comments'));

        expect(mockOnUpdate).toHaveBeenCalledTimes(1);
        const updateCall = mockOnUpdate.mock.calls[0][0];
        expect(updateCall.comments).toContain('Existing comments');
        expect(updateCall.comments).toContain('**Salary Calculation**');
        expect(updateCall.comments).toContain('Mode: Classic');
        expect(updateCall.comments).toContain('Gross/year: 88000.00');
    });

    it('should replace existing salary calculation when saving new one', async () => {
        const mockOnUpdate = vi.fn();
        const jobWithCalc = {
            ...mockJob,
            comments: `Some notes
---
**Salary Calculation** (1/1/2025, 10:00:00 AM)
Mode: Classic | Rate: 30 (Hourly) | Freelance: 80
- Gross/year: 60000.00
- Tax/year: 10000
- Net/year: 50000
- Net/month: 4166

More comments`,
        };

        (salaryApi.calculate as any).mockResolvedValue(mockSalaryResponse({
            gross_year: '88000.00',
            net_month: '5833',
        }));

        render(<SalaryCalculator job={jobWithCalc as any} onUpdate={mockOnUpdate} />);
        await waitForDebounce();

        fireEvent.click(screen.getByText('💾 Save to Comments'));

        const updateCall = mockOnUpdate.mock.calls[0][0];
        expect(updateCall.comments).toContain('Some notes');
        expect(updateCall.comments).toContain('More comments');
        expect(updateCall.comments).toContain('Gross/year: 88000.00');
        expect(updateCall.comments).not.toContain('Gross/year: 60000.00');
        expect(updateCall.comments).not.toContain('Rate: 30 (Hourly)');
    });
});
