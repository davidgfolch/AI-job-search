import { act } from '@testing-library/react';
import { vi } from 'vitest';

export const mockSalaryResponse = (overrides = {}) => ({
    gross_year: '5000',
    parsed_equation: 'eq',
    year_tax: '200',
    year_tax_equation: 'tax_eq',
    net_year: '800',
    net_month: '66',
    freelance_tax: '50',
    ...overrides,
});

export const waitForDebounce = async () => {
    act(() => {
        vi.advanceTimersByTime(600);
    });
    await act(async () => { await Promise.resolve(); });
};

export const skipInitialCalculation = () => {
    act(() => {
        vi.advanceTimersByTime(600);
    });
};

export const mockJob = {
    id: '123',
    title: 'Test Job',
    comments: 'Existing comments',
};
