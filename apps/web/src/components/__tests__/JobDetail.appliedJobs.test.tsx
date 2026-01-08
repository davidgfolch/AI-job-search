import { screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient } from '@tanstack/react-query';
import JobDetail from '../JobDetail';
import { jobsApi } from '../../api/jobs';
import { renderWithProviders, createMockJob } from '../../__tests__/test-utils';

vi.mock('../../api/jobs', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn(),
    },
}));

const mockJob = createMockJob({
    company: 'Tech Corp',
    client: 'Client A',
});

describe('JobDetail - Applied Jobs', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([]);
    });

    it('displays applied company jobs indicator when jobs exist', async () => {
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockResolvedValueOnce([
            { id: 2, created: '2024-01-15T10:00:00' },
            { id: 3, created: '2024-02-20T15:30:00' },
        ]);
        renderWithProviders(<JobDetail job={mockJob} />);
        await screen.findByText(/already applied/);
        const link = screen.getByText(/already applied to 2/);
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute('href', '/?ids=2,3');
        expect(link).toHaveAttribute('target', '_blank');
        expect(screen.getByText(/15-01-24/)).toBeInTheDocument();
        expect(screen.getByText(/20-02-24/)).toBeInTheDocument();
    });

    it('does not display indicator when no applied jobs exist', async () => {
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockResolvedValue([]);
        renderWithProviders(<JobDetail job={mockJob} />);
        // Wait for potential rendering
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        expect(screen.queryByText(/already applied/)).not.toBeInTheDocument();
    });

    it('handles API error gracefully', async () => {
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockRejectedValueOnce(new Error('API Error'));
        renderWithProviders(<JobDetail job={mockJob} />);
        // Wait for potential effects
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        // Should simply not show the indicator
        expect(screen.queryByText(/already applied/)).not.toBeInTheDocument();
    });

    it('truncates applied jobs list if more than 60', async () => {
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        // Generate 65 mock jobs
        const manyJobs = Array.from({ length: 65 }, (_, i) => ({ 
            id: i + 1, 
            created: '2024-01-01' 
        }));
        mockGetAppliedJobsByCompany.mockResolvedValue(manyJobs);
        renderWithProviders(<JobDetail job={mockJob} />);
        // Wait for it to appear
        const link = await screen.findByTitle(/Open in new tab showing these specific jobs/);
        expect(link).toBeInTheDocument();
        expect(link).toHaveTextContent(/already applied to 60/);
        // Check for truncation indicator '...'
        // The component logic sets created = '...' for the last element (index 59)
        // We look for this text
        expect(screen.getByText('...')).toBeInTheDocument();
    });

    it('makes only one API call when re-rendered with the same job', async () => {
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockClear();
        mockGetAppliedJobsByCompany.mockResolvedValue([]);
        const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
        const { rerender } = renderWithProviders(<JobDetail job={mockJob} />, { queryClient });
        // Wait for initial fetch
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        // Rerender with SAME job
        rerender(<JobDetail job={mockJob} />);
        // Wait for potential effects
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        // Should be called exactly once
        expect(mockGetAppliedJobsByCompany).toHaveBeenCalledTimes(1);
    });
});
