import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SalaryHistoryModal from '../SalaryHistoryModal';
import { jobsApi, type Job, type SalaryHistoryEntry } from '../../../api/ViewerApi';
import { renderWithProviders } from '../../../test/test-utils';

vi.mock('../../../api/ViewerApi', () => ({
    jobsApi: { deleteSalaryHistoryEntry: vi.fn() },
}));

const job = { id: 7, company: 'Acme' } as unknown as Job;

const entry = (overrides: Partial<SalaryHistoryEntry> = {}): SalaryHistoryEntry => ({
    id: 'a1',
    job_id: 7,
    company_raw: 'Acme',
    company_normalized: 'acme',
    title: 'Developer',
    salary: '50k',
    recorded_at: '2026-01-01T10:00:00',
    source: 'LinkedIn',
    ...overrides,
});

describe('SalaryHistoryModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.restoreAllMocks();
    });

    it('renders a delete button for every history row', () => {
        renderWithProviders(
            <SalaryHistoryModal job={job} isOpen onClose={vi.fn()} records={[entry(), entry({ id: 'a2', salary: '60k' })]} />,
        );
        expect(screen.getAllByTitle('Delete salary history entry')).toHaveLength(2);
        expect(screen.getByText('50k')).toBeInTheDocument();
        expect(screen.getByText('60k')).toBeInTheDocument();
    });

    it('deletes the selected entry from the database', async () => {
        vi.mocked(jobsApi.deleteSalaryHistoryEntry).mockResolvedValue({ deleted: 1 });
        renderWithProviders(
            <SalaryHistoryModal job={job} isOpen onClose={vi.fn()} records={[entry(), entry({ id: 'a2', salary: '60k' })]} />,
        );

        fireEvent.click(screen.getAllByTitle('Delete salary history entry')[1]);
        fireEvent.click(screen.getByText('Confirm'));

        await waitFor(() => expect(jobsApi.deleteSalaryHistoryEntry).toHaveBeenCalledWith('a2'));
    });

    it('asks for confirmation in a modal dialog', () => {
        renderWithProviders(
            <SalaryHistoryModal job={job} isOpen onClose={vi.fn()} records={[entry()]} />,
        );

        expect(screen.queryByText('Delete the 50k entry for Acme?')).not.toBeInTheDocument();

        fireEvent.click(screen.getByTitle('Delete salary history entry'));

        expect(screen.getByText('Delete the 50k entry for Acme?')).toBeInTheDocument();
        expect(screen.getByText('Confirm')).toBeInTheDocument();
        expect(jobsApi.deleteSalaryHistoryEntry).not.toHaveBeenCalled();
    });

    it('does not delete when the confirmation is dismissed', () => {
        renderWithProviders(
            <SalaryHistoryModal job={job} isOpen onClose={vi.fn()} records={[entry()]} />,
        );

        fireEvent.click(screen.getByTitle('Delete salary history entry'));
        fireEvent.click(screen.getByText('Cancel'));

        expect(jobsApi.deleteSalaryHistoryEntry).not.toHaveBeenCalled();
        expect(screen.queryByText('Delete the 50k entry for Acme?')).not.toBeInTheDocument();
    });

    it('shows the error when the deletion fails', async () => {
        vi.mocked(jobsApi.deleteSalaryHistoryEntry).mockRejectedValue(new Error('Error deleting salary history entry: boom'));
        renderWithProviders(
            <SalaryHistoryModal job={job} isOpen onClose={vi.fn()} records={[entry()]} />,
        );

        fireEvent.click(screen.getByTitle('Delete salary history entry'));
        fireEvent.click(screen.getByText('Confirm'));

        expect(await screen.findByText('Error deleting salary history entry: boom')).toBeInTheDocument();
    });

    it('shows the empty state when there is no history', () => {
        renderWithProviders(<SalaryHistoryModal job={job} isOpen onClose={vi.fn()} records={[]} />);
        expect(screen.getByText(/No salary history recorded yet/)).toBeInTheDocument();
    });

    it('renders nothing while closed', () => {
        const { container } = renderWithProviders(
            <SalaryHistoryModal job={job} isOpen={false} onClose={vi.fn()} records={[entry()]} />,
        );
        expect(container).toBeEmptyDOMElement();
    });
});
