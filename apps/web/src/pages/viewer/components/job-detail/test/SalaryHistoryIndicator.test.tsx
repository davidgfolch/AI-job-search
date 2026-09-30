import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SalaryHistoryIndicator from '../SalaryHistoryIndicator';
import type { Job } from '../../api/ViewerApi';

const mockUseHistory = vi.hoisted(() => vi.fn());
vi.mock('../../../hooks/useSalaryHistory', () => ({ useCompanySalaryHistory: (company: string) => mockUseHistory(company) }));

const mockOnClose = vi.hoisted(() => vi.fn());
vi.mock('../SalaryHistoryModal', () => ({
    default: ({ isOpen, onClose, records }: { isOpen: boolean; onClose: () => void; records: unknown[] }) =>
        isOpen ? <div data-testid="salary-modal" data-records={records.length}><button onClick={onClose}>close-modal</button></div> : null,
}));

const job = { id: 1, company: 'Acme' } as unknown as Job;

describe('SalaryHistoryIndicator', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the loading placeholder and queries by company', () => {
        mockUseHistory.mockReturnValue({ data: undefined, isLoading: true });
        const { container } = render(<SalaryHistoryIndicator job={job} />);
        expect(mockUseHistory).toHaveBeenCalledWith('Acme');
        expect(container.querySelector('.loading-dots')).toBeInTheDocument();
    });

    it.each([
        ['no data', undefined],
        ['an empty history', []],
    ])('renders nothing when there is %s', (_label, history) => {
        mockUseHistory.mockReturnValue({ data: history, isLoading: false });
        const { container } = render(<SalaryHistoryIndicator job={job} />);
        expect(container.querySelector('.info-row')).toBeNull();
    });

    it('lists up to three distinct salaries and the company count', () => {
        mockUseHistory.mockReturnValue({
            data: [
                { salary: 10, company_raw: 'Acme' },
                { salary: 20, company_raw: 'Acme Inc' },
            ],
            isLoading: false,
        });
        render(<SalaryHistoryIndicator job={job} />);
        expect(screen.getByText('10 | 20')).toBeInTheDocument();
        expect(screen.getByText('(2 companies)')).toBeInTheDocument();
    });

    it('collapses distinct salaries to one entry and omits the company count', () => {
        mockUseHistory.mockReturnValue({
            data: [
                { salary: 10, company_raw: 'Acme' },
                { salary: 10, company_raw: 'Acme' },
            ],
            isLoading: false,
        });
        render(<SalaryHistoryIndicator job={job} />);
        expect(screen.getByText('10')).toBeInTheDocument();
        expect(screen.queryByText(/companies/)).not.toBeInTheDocument();
    });

    it('appends an ellipsis when there are more than three distinct salaries', () => {
        mockUseHistory.mockReturnValue({
            data: [10, 20, 30, 40].map(salary => ({ salary, company_raw: 'Acme' })),
            isLoading: false,
        });
        render(<SalaryHistoryIndicator job={job} />);
        expect(screen.getByText(/^10 \| 20 \| 30\.\.\.$/)).toBeInTheDocument();
    });

    it('opens and closes the modal from the history button', () => {
        mockUseHistory.mockReturnValue({ data: [{ salary: 10, company_raw: 'Acme' }], isLoading: false });
        render(<SalaryHistoryIndicator job={job} />);
        expect(screen.queryByTestId('salary-modal')).not.toBeInTheDocument();
        fireEvent.click(screen.getByTitle('View full history'));
        expect(screen.getByTestId('salary-modal')).toHaveAttribute('data-records', '1');
        fireEvent.click(screen.getByRole('button', { name: 'close-modal' }));
        expect(screen.queryByTestId('salary-modal')).not.toBeInTheDocument();
    });
});