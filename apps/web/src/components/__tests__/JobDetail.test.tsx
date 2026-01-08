import { screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import JobDetail from '../JobDetail';
import type { Job } from '../../api/jobs';
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
    markdown: 'Job Description Content',
    required_technologies: 'React, TypeScript',
    comments: 'Initial comment',
});



describe('JobDetail', () => {
    beforeEach(() => {
        vi.resetAllMocks();
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([]);
    });

    it('renders job details correctly', async () => {
        renderWithProviders(<JobDetail job={mockJob} />);
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
        renderWithProviders(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        const link = screen.getByText('Software Engineer');
        expect(link).toHaveAttribute('href', 'http://example.com');
        expect(link).toHaveAttribute('target', '_blank');
    });

    it('displays CV match percentage when available', async () => {
        renderWithProviders(<JobDetail job={mockJob} />);
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
        renderWithProviders(<JobDetail job={jobWithoutOptionals} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        // These should not appear in the document
        expect(screen.queryByText('Company:')).not.toBeInTheDocument();
        expect(screen.queryByText('100k')).not.toBeInTheDocument();
        expect(screen.queryByText('Initial comment')).not.toBeInTheDocument();
    });






    it('calls onUpdate with null salary when delete button is clicked', async () => {
        const onUpdateMock = vi.fn();
        renderWithProviders(<JobDetail job={mockJob} onUpdate={onUpdateMock} />);
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
        renderWithProviders(<JobDetail job={jobWithStatuses} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        expect(screen.getByText('easy apply')).toBeInTheDocument();
        expect(screen.getByText('ai enriched')).toBeInTheDocument();
        expect(screen.getByText('interview')).toBeInTheDocument();
    });


    it('toggles salary calculator visibility', async () => {
        renderWithProviders(<JobDetail job={mockJob} />);
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
        renderWithProviders(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        const grossButton = screen.getByText('🧮 Gross year');
        fireEvent.click(grossButton);
        expect(windowOpenSpy).toHaveBeenCalledWith('https://tecalculo.com/calculadora-de-sueldo-neto', '_blank');
        windowOpenSpy.mockRestore();
    });


    it('displays created and modified dates with time, ignoring differences under 5 minutes', async () => {
        const jobWithDates: Job = {
            ...mockJob,
            company: 'Test Co', // Ensure company exists to satisfy some conditional rendering
            web_page: 'http://example.com', // Ensure web_page exists so dates are shown
            created: '2023-01-01T10:00:00',
            modified: '2023-01-01T10:04:59', // Difference under 5 minutes, should NOT show modified
        };
        const { rerender } = renderWithProviders(<JobDetail job={jobWithDates} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        
        // Should show created date with time
        // Note: toLocaleString format depends on env, but typically includes date and time.
        // We will check if it contains the time part.
        // 10:00 is expected.
        const createdRegex = /10:00/; 
        expect(screen.getByText(createdRegex)).toBeInTheDocument();
        
        // Should NOT show modified because difference is under 5 minutes
        expect(screen.queryByText(/modified/)).not.toBeInTheDocument();

        // Update modified to be 5 minutes or more different
        const jobModifiedLater: Job = {
            ...jobWithDates,
            modified: '2023-01-01T10:05:00',
        };
        
        rerender(<JobDetail job={jobModifiedLater} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        
        // Should show modified now (5 minutes or more difference)
        expect(screen.getAllByText(/modified/)[0]).toBeInTheDocument();
        // Should show time 10:05
        expect(screen.getByText(/10:05/)).toBeInTheDocument();
    });

    it('displays delete button when onDelete prop is provided', async () => {
        const onDeleteMock = vi.fn();
        renderWithProviders(<JobDetail job={mockJob} onDelete={onDeleteMock} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        
        const deleteButton = screen.getByTitle('Delete this job');
        expect(deleteButton).toBeInTheDocument();
        expect(deleteButton).toHaveTextContent('🗑️ Delete');
    });

    it('calls onDelete when delete button is clicked', async () => {
        const onDeleteMock = vi.fn();
        renderWithProviders(<JobDetail job={mockJob} onDelete={onDeleteMock} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        
        const deleteButton = screen.getByTitle('Delete this job');
        deleteButton.click();
        
        expect(onDeleteMock).toHaveBeenCalledTimes(1);
    });

    it('does not display delete button when onDelete prop is not provided', async () => {
        renderWithProviders(<JobDetail job={mockJob} />);
        await waitFor(() => new Promise(resolve => setTimeout(resolve, 0)));
        
        expect(screen.queryByTitle('Delete this job')).not.toBeInTheDocument();
    });
});

