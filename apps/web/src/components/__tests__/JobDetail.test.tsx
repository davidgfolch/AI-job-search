import { render, screen, waitFor } from '@testing-library/react';
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
});

