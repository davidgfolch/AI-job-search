import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jobsApi } from '../../api/jobs';
import { mockJobs, renderViewer, waitForAsync } from './ViewerTestUtils';
import { mockJobsApiDefault, waitForJobList, selectJob, switchToTab, clickFilterButton, verifyJobDetails, verifySummary, triggerInfiniteScroll } from './ViewerTestHelpers';

// --- Mocks ---
let observerCallback: any;
globalThis.IntersectionObserver = vi.fn(function(this: any, cb) {
    observerCallback = cb;
    return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
}) as any;

vi.mock('../../api/jobs', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn().mockResolvedValue([]),
    },
}));

vi.mock('../../hooks/viewer/useJobUpdates', () => ({
    useJobUpdates: vi.fn().mockReturnValue({ hasNewJobs: false, newJobsCount: 0 }),
}));

// --- Tests ---
describe('Viewer', () => {
    beforeEach(() => { vi.clearAllMocks(); });
    
    const stateTestCases = [
        {
            name: 'renders loading state initially',
            mockSetup: () => (jobsApi.getJobs as any).mockReturnValue(new Promise(() => { })),
            assertion: async () => {
                expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
                await waitForAsync();
            }
        },
        {
            name: 'renders job list after loading',
            mockSetup: () => (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 }),
            assertion: async () => {
                await waitForJobList();
                verifySummary(/2\/2 loaded \| 0 Selected/);
            }
        },
        {
            name: 'handles error state',
            mockSetup: () => (jobsApi.getJobs as any).mockRejectedValue(new Error('Failed to fetch')),
            assertion: async () => await waitFor(() => expect(screen.getByText('Failed to fetch')).toBeInTheDocument())
        }
    ];
    
    it.each(stateTestCases)('$name', async ({ mockSetup, assertion }) => {
        mockSetup();
        renderViewer();
        await assertion();
    });

    it('handles user interactions: select, verify details, partial filter', async () => {
        mockJobsApiDefault();
        renderViewer();
        await waitForJobList();
        expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
        selectJob('Job 1');
        verifyJobDetails('Description 1', 'Company 1');
        clickFilterButton('Flagged');
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ flagged: true, page: 1 })));
        await waitForAsync();
    });

    it('handles tab switching and edit interactions', async () => {
        mockJobsApiDefault();
        renderViewer();
        await waitForJobList();
        selectJob('Job 1');
        switchToTab('Edit');
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();
        switchToTab('List');
        expect(screen.getByRole('cell', { name: 'Job 1' })).toBeInTheDocument();
        await waitForAsync();
    });

    it('handles infinite scroll', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 50, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => verifySummary(/2\/50 loaded \| 0 Selected/));
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(1);
    });

    it('updates job and refreshes list (isolated)', async () => {
        mockJobsApiDefault();
        (jobsApi.updateJob as any).mockResolvedValue({ ...mockJobs[0], flagged: true });
        renderViewer();
        await waitForJobList();
        selectJob('Job 1');
        switchToTab('Edit');
        const flaggedPills = screen.getAllByText('Flagged');
        fireEvent.click(flaggedPills[flaggedPills.length - 1]);
        await waitFor(() => expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { flagged: true }));
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(2);
        await waitForAsync();
    });

    it('filters by URL ids', async () => {
        mockJobsApiDefault();
        renderViewer(['/?ids=1,2']);
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ sql_filter: 'id IN (1,2)', page: 1 })));
    });

    it('refreshes list when clicking List tab if new jobs exist', async () => {
        const { useJobUpdates } = await import('../../hooks/viewer/useJobUpdates');
        (useJobUpdates as any).mockReturnValue({ hasNewJobs: true, newJobsCount: 5 });
        mockJobsApiDefault();
        renderViewer();
        await waitForJobList();
        selectJob('Job 1');
        switchToTab('Edit');
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();
        (jobsApi.getJobs as any).mockClear();
        const reloadBtn = screen.getByText((content, element) => element?.tagName.toLowerCase() === 'button' && content.includes('new'));
        fireEvent.click(reloadBtn);
        // hardRefresh calls queryClient.resetQueries which triggers a refetch that ultimately calls jobsApi.getJobs
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalled());
    });

    it('validates configuration name on save', async () => {
        mockJobsApiDefault();
        renderViewer();
        await waitForJobList();
        fireEvent.click(screen.getByText(/Filters/));
        fireEvent.click(screen.getByText('Save'));
        await waitFor(() => expect(screen.getByText('Please enter a name for the configuration')).toBeInTheDocument());
        fireEvent.click(screen.getByText('Please enter a name for the configuration'));
        await waitFor(() => expect(screen.queryByText('Please enter a name for the configuration')).not.toBeInTheDocument());
    });

    it('calls getAppliedJobsByCompany exactly once when selecting a job', async () => {
        mockJobsApiDefault();
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([{ id: 999, created: '2024-01-01' }]);
        renderViewer();
        await waitForJobList();
        (jobsApi.getAppliedJobsByCompany as any).mockClear();
        selectJob('Job 1');
        await waitFor(() => expect(screen.getByText(/already applied/i)).toBeInTheDocument());
        expect(jobsApi.getAppliedJobsByCompany).toHaveBeenCalledTimes(1);
    });

    it('loads job details when clicking a job loaded via infinite scroll', async () => {
        (jobsApi.getJobs as any).mockResolvedValueOnce({ items: mockJobs, total: 4, page: 1, size: 2 });
        const page2Jobs = [
            { id: 3, title: 'Job 3', company: 'Company 3', description: 'Desc 3', date: '2024-01-02', markdown: 'Desc 3', created: '2024-01-02' },
            { id: 4, title: 'Job 4', company: 'Company 4', description: 'Desc 4', date: '2024-01-02', markdown: 'Desc 4', created: '2024-01-02' }
        ];
        (jobsApi.getJobs as any).mockResolvedValueOnce({ items: page2Jobs, total: 4, page: 2, size: 2 });
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([]);
        renderViewer();
        await waitForJobList();
        expect(observerCallback).toBeDefined();
        await triggerInfiniteScroll(observerCallback);
        await waitFor(() => expect(screen.getByText('Job 3')).toBeInTheDocument());
        selectJob('Job 3');
        await waitFor(() => expect(screen.getByText('Desc 3', { selector: '.markdown-content p' })).toBeInTheDocument());
    });
});
