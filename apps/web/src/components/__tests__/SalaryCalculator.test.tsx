import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import SalaryCalculator from '../SalaryCalculator';
import { salaryApi } from '../../api/salary';

vi.mock('../../api/salary', () => ({
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
        (salaryApi.calculate as any).mockResolvedValue({
            gross_year: '1000',
            parsed_equation: 'eq',
            year_tax: '200',
            year_tax_equation: 'tax_eq',
            net_year: '800',
            net_month: '66',
            freelance_tax: '50',
        });

        render(<SalaryCalculator />);

        const rateInput = screen.getByRole('spinbutton');
        fireEvent.change(rateInput, { target: { value: '50' } });

        // Should not have called yet
        expect(salaryApi.calculate).not.toHaveBeenCalled();

        act(() => {
            vi.advanceTimersByTime(600);
        });
        await act(async () => { await Promise.resolve(); });

        expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining({
            rate: 50,
        }));

        expect(screen.getByText('1000')).toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        (salaryApi.calculate as any).mockRejectedValue(new Error('API Error'));

        render(<SalaryCalculator />);
        
        // Wait for initial call (on mount)
        // Wait for initial call (on mount)
        act(() => {
            vi.advanceTimersByTime(600);
        });
        
        (salaryApi.calculate as any).mockClear();
        
        const rateInput = screen.getByRole('spinbutton');
        fireEvent.change(rateInput, { target: { value: '60' } });
        
        act(() => {
            vi.advanceTimersByTime(600);
        });
        await act(async () => { await Promise.resolve(); });
        
        expect(salaryApi.calculate).toHaveBeenCalled();
        
        expect(consoleSpy).toHaveBeenCalledWith('Error calculating salary:', expect.any(Error));
        consoleSpy.mockRestore();
    });

    it('should update other inputs correctly', async () => {
        (salaryApi.calculate as any).mockResolvedValue({
            gross_year: '1000',
            parsed_equation: 'eq',
            year_tax: '200',
            year_tax_equation: 'tax_eq',
            net_year: '800',
            net_month: '66',
            freelance_tax: '50',
        });

        render(<SalaryCalculator />);
        
        // Wait for initial
        // Wait for initial
        act(() => {
            vi.advanceTimersByTime(600);
        });
        (salaryApi.calculate as any).mockClear();

        (salaryApi.calculate as any).mockResolvedValue({
            gross_year: '9999',
            parsed_equation: 'eq',
            year_tax: '200',
            year_tax_equation: 'tax_eq',
            net_year: '800',
            net_month: '66',
            freelance_tax: '50',
        });

        const selects = screen.getAllByRole('combobox');
        const typeSelect = selects[0];
        const freelanceSelect = selects[1]; 

        fireEvent.change(typeSelect, { target: { value: 'Daily' } });
        fireEvent.change(freelanceSelect, { target: { value: '300' } });

        act(() => {
            vi.advanceTimersByTime(600);
        });
        await act(async () => { await Promise.resolve(); });

        expect(screen.getByText('9999')).toBeInTheDocument();

        expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining({
            rate_type: 'Daily',
            freelance_rate: 300,
        }));
    });
});
