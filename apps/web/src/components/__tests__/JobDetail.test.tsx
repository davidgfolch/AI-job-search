import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import JobDetail from '../JobDetail';
import type { Job } from '../../api/jobs';
import { createMockJob } from '../../__tests__/test-utils';

vi.mock('../../api/jobs', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn().mockResolvedValue([]),
    },
}));

const mockJob = createMockJob({
    markdown: 'Job Description Content',
    required_technologies: 'React, TypeScript',
    comments: 'Initial comment',
});

describe('JobDetail', () => {
    it('renders job details correctly', async () => {
        render(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        expect(screen.getByText('Software Engineer')).toBeInTheDocument();
        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
        expect(screen.getByText('Job Description Content')).toBeInTheDocument();
        expect(screen.getByText('React, TypeScript')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Initial comment')).toBeInTheDocument();
    });

    it('renders job link correctly', async () => {
        render(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        const link = screen.getByText('Software Engineer');
        expect(link).toHaveAttribute('href', 'http://example.com');
        expect(link).toHaveAttribute('target', '_blank');
    });

    it('displays CV match percentage when available', async () => {
        render(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        expect(screen.getByText('90%')).toBeInTheDocument();
    });

    it('does not display optional fields when they are null', async () => {
        const jobWithoutOptionals: Job = {
            ...mockJob,
            company: null,
            salary: null,
            comments: null,
            optional_technologies: null,
        };
        render(<JobDetail job={jobWithoutOptionals} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        // These should not appear in the document
        expect(screen.queryByText('Company:')).not.toBeInTheDocument();
        expect(screen.queryByText('100k')).not.toBeInTheDocument();
        expect(screen.queryByText('Initial comment')).not.toBeInTheDocument();
    });

    it('displays applied company jobs indicator when jobs exist', async () => {
        const { jobsApi } = await import('../../api/jobs');
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockResolvedValueOnce([
            { id: 2, created: '2024-01-15T10:00:00' },
            { id: 3, created: '2024-02-20T15:30:00' },
        ]);
        render(<JobDetail job={mockJob} />);
        await screen.findByText(/already applied/);
        const link = screen.getByText(/already applied to 2/);
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute('href', '/?ids=2,3');
        expect(link).toHaveAttribute('target', '_blank');
        expect(screen.getByText(/15-01-24/)).toBeInTheDocument();
        expect(screen.getByText(/20-02-24/)).toBeInTheDocument();
    });

    it('does not display indicator when no applied jobs exist', async () => {
        const { jobsApi } = await import('../../api/jobs');
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockResolvedValueOnce([]);
        render(<JobDetail job={mockJob} />);
        // Wait for the async effect to complete (state update) to avoid act warning
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        expect(screen.queryByText(/already applied/)).not.toBeInTheDocument();
    });

    it('handles API error gracefully', async () => {
        const { jobsApi } = await import('../../api/jobs');
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockRejectedValueOnce(new Error('API Error'));
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
        render(<JobDetail job={mockJob} />);
        // Wait for the error log, which confirms the catch block and state updates have run
        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith('Error fetching applied company jobs:', expect.any(Error));
        });
        expect(screen.queryByText(/already applied/)).not.toBeInTheDocument();
        consoleSpy.mockRestore();
    });
    it('calls onUpdate with null salary when delete button is clicked', async () => {
        const onUpdateMock = vi.fn();
        render(<JobDetail job={mockJob} onUpdate={onUpdateMock} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        const deleteButton = screen.getByTitle('Delete salary information');
        expect(deleteButton).toBeInTheDocument();
        deleteButton.click();
        expect(onUpdateMock).toHaveBeenCalledWith({ salary: null });
    });

    it('displays active boolean statuses', async () => {
        const jobWithStatuses: Job = {
            ...mockJob,
            easy_apply: true,
            ai_enriched: true,
            interview: true,
        };
        render(<JobDetail job={jobWithStatuses} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        expect(screen.getByText('easy apply')).toBeInTheDocument();
        expect(screen.getByText('ai enriched')).toBeInTheDocument();
        expect(screen.getByText('interview')).toBeInTheDocument();
    });
    it('truncates applied jobs list if more than 60', async () => {
        const { jobsApi } = await import('../../api/jobs');
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        // Generate 65 mock jobs
        const manyJobs = Array.from({ length: 65 }, (_, i) => ({ 
            id: i + 1, 
            created: '2024-01-01' 
        }));
        mockGetAppliedJobsByCompany.mockResolvedValueOnce(manyJobs);
        render(<JobDetail job={mockJob} />);
        await screen.findByText(/already applied to 60/); // Should show truncated count or logic? 
        // Logic says: jobs.length > 60 -> jobs.splice(60).
        // So displayed length should be 60? 
        // Wait, the link text says `already applied to ${appliedCompanyJobs.length}`.
        // If splice(60) is called, length becomes 60.
        expect(screen.getByText(/already applied to 60/)).toBeInTheDocument();
        // Verify the 60th item (index 59) has '...' as created date
        // Wait, original code: jobs[60 - 1].created = '...'; -> index 59.
        // The list renders appliedCompanyJobs.map...
        // We look for '...' in the rendered output.
        // The component renders: aj.created?.startsWith('...') ? aj.created : ...
        // So we should see '...'
        expect(screen.getByText('...')).toBeInTheDocument();
    });

    it('toggles salary calculator visibility', async () => {
        render(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        const calcButton = screen.getByText('🧮 Freelance');
        fireEvent.click(calcButton);
        expect(screen.getByText('Salary Calculator')).toBeInTheDocument();
        const closeButton = screen.getByLabelText('Close calculator');
        fireEvent.click(closeButton);
        expect(screen.queryByText('Salary Calculator')).not.toBeInTheDocument();
    });

    it('opens gross salary calculator in new tab', async () => {
        const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
        render(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        const grossButton = screen.getByText('🧮 Gross year');
        fireEvent.click(grossButton);
        expect(windowOpenSpy).toHaveBeenCalledWith('https://tecalculo.com/calculadora-de-sueldo-neto', '_blank');
        windowOpenSpy.mockRestore();
    });

    it('makes only one API call when re-rendered with the same job', async () => {
        const { jobsApi } = await import('../../api/jobs');
        const mockGetAppliedJobsByCompany = jobsApi.getAppliedJobsByCompany as any;
        mockGetAppliedJobsByCompany.mockClear();
        mockGetAppliedJobsByCompany.mockResolvedValue([]);
        const { rerender } = render(<JobDetail job={mockJob} />);
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

