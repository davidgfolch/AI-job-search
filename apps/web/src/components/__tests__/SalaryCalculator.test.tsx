import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SalaryCalculator from '../SalaryCalculator';
import { salaryApi } from '../../api/salary';

vi.mock('../../api/salary', () => ({
    salaryApi: {
        calculate: vi.fn(),
    },
}));

describe('SalaryCalculator', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const waitDebounce = () => new Promise(resolve => setTimeout(resolve, 600));

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

        await waitFor(async () => {
            expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining({
                rate: 50,
            }));
        }, { timeout: 2000 });

        expect(screen.getByText('1000')).toBeInTheDocument();
    });

    it('should handle API errors gracefully', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        (salaryApi.calculate as any).mockRejectedValue(new Error('API Error'));

        render(<SalaryCalculator />);
        
        // Wait for initial call (on mount)
        await act(async () => {
            await waitDebounce();
        });
        
        (salaryApi.calculate as any).mockClear();
        
        const rateInput = screen.getByRole('spinbutton');
        fireEvent.change(rateInput, { target: { value: '60' } });
        
        await waitFor(() => {
            expect(salaryApi.calculate).toHaveBeenCalled();
        }, { timeout: 2000 });
        
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
        await act(async () => {
             await waitDebounce();
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

        expect(await screen.findByText('9999')).toBeInTheDocument();

        expect(salaryApi.calculate).toHaveBeenCalledWith(expect.objectContaining({
            rate_type: 'Daily',
            freelance_rate: 300,
        }));
    });
});
