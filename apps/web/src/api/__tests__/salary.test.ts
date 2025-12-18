import { describe, it, expect, vi, beforeEach } from 'vitest';
import { salaryApi, type SalaryCalculationRequest } from '../salary';

const { mockPost } = vi.hoisted(() => {
    return { mockPost: vi.fn() };
});

// Mock axios
vi.mock('axios', () => {
    return {
        default: {
            create: vi.fn(() => ({
                post: mockPost,
                get: vi.fn(),
            })),
        },
    };
});

describe('salaryApi', () => {

    beforeEach(() => {
        mockPost.mockClear();
    });

    const mockRequest: SalaryCalculationRequest = {
        rate: 50,
        rate_type: 'Hourly',
        hours_x_day: 8,
        freelance_rate: 60,
    };

    const mockResponse = {
        gross_year: '100000',
        parsed_equation: '50 * 8 * ...',
        year_tax: '20000',
        year_tax_equation: '...',
        net_year: '80000',
        net_month: '6666',
        freelance_tax: '500',
    };

    it('should calculate salary successfully', async () => {
        mockPost.mockResolvedValueOnce({ data: mockResponse });

        const result = await salaryApi.calculate(mockRequest);

        expect(mockPost).toHaveBeenCalledWith('/salary/calculate', mockRequest);
        expect(result).toEqual(mockResponse);
    });

    it('should handle errors correctly', async () => {
        const errorMessage = 'Network Error';
        mockPost.mockRejectedValueOnce(new Error(errorMessage));

        await expect(salaryApi.calculate(mockRequest)).rejects.toThrow(
            `Error calculating salary: ${errorMessage}`
        );
    });

    it('should handle non-Error objects thrown', async () => {
        mockPost.mockRejectedValueOnce('Some string error');

        await expect(salaryApi.calculate(mockRequest)).rejects.toThrow(
            'Error calculating salary: Some string error'
        );
    });
});
