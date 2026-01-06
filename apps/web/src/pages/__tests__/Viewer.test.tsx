import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jobsApi } from '../../api/jobs';
import { mockJobs, renderViewer, waitForAsync } from './ViewerTestUtils';

// --- Mocks ---
globalThis.IntersectionObserver = vi.fn(function (this: any) {
    this.observe = vi.fn();
    this.unobserve = vi.fn();
    this.disconnect = vi.fn();
}) as any;

// Correctly mock the module and its export 'jobsApi'
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
                await waitFor(() => {
                    expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
                    expect(screen.getAllByText('Job 2').length).toBeGreaterThan(0);
                });
                const summary = screen.getByText(/ loaded \| /);
                expect(summary).toHaveTextContent(/2\/2 loaded \| 0 Selected/);
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
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));

        // Interaction: Select Job
        expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        expect(screen.getByText('Description 1')).toBeInTheDocument();
        expect(screen.getAllByText('Company 1')).toHaveLength(2);

        // Interaction: Filter (Flagged)
        const flaggedButtons = screen.getAllByRole('button', { name: /Flagged/i });
        fireEvent.click(flaggedButtons[0]);
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ flagged: true, page: 1 })));
        
        await waitForAsync();
    });

    it('handles tab switching and edit interactions', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));
        // Select and Switch to Edit
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        fireEvent.click(screen.getByText('Edit'));
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();
        // Switch back to List
        fireEvent.click(screen.getByText('List'));
        expect(screen.getByRole('cell', { name: 'Job 1' })).toBeInTheDocument();
        await waitForAsync();
    });

    it('handles infinite scroll', async () => {
         // Infinite Scroll
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 50, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => {
            const summary = screen.getByText(/ loaded \| /);
            expect(summary).toHaveTextContent(/2\/50 loaded \| 0 Selected/);
        });
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(1);
    });

    it('updates job and refreshes list (isolated)', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
        (jobsApi.updateJob as any).mockResolvedValue({ ...mockJobs[0], flagged: true });
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        fireEvent.click(screen.getByText('Edit'));
        const flaggedPills = screen.getAllByText('Flagged');
        fireEvent.click(flaggedPills[flaggedPills.length - 1]);
        await waitFor(() => expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { flagged: true }));
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(2);
        await waitForAsync();
    });

    it('filters by URL ids', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer(['/?ids=1,2']);
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ sql_filter: 'id IN (1,2)', page: 1 })));
    });

    it('refreshes list when clicking List tab if new jobs exist', async () => {
        const { useJobUpdates } = await import('../../hooks/viewer/useJobUpdates');
        (useJobUpdates as any).mockReturnValue({ hasNewJobs: true, newJobsCount: 5 });
        // Mock refetch behavior via getJobs or however useViewer calls it.
        // useViewer calls actions.refreshJobs which calls refetch() from useJobsData.
        // We mocked jobsApi, but useJobsData uses useQuery which calls jobsApi.
        // We need to ensure that when refresh happens, something observable occurs.
        // When refreshJobs is called:
        // 1. If page != 1, it sets page=1.
        // 2. If page == 1, it calls refetch() then selects first job.
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));
        // Select a job first
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        // Switch to Edit tab so we can switch back to List
        fireEvent.click(screen.getByText('Edit'));
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();
        // Now click List tab. Since hasNewJobs=true, it should trigger refresh.
        // We can check if jobsApi.getJobs was called extra times or with specific params?
        // useQuery refetch usually calls the queryFn.
        (jobsApi.getJobs as any).mockClear(); // Clear previous calls
        const listBtn = screen.getByText((content, element) => element?.tagName.toLowerCase() === 'button' && content.includes('List'));
        fireEvent.click(listBtn);
        // Expect getJobs to be called for refresh
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalled());
    });

    it('validates configuration name on save', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));
        fireEvent.click(screen.getByText(/Filters/));
        fireEvent.click(screen.getByText('Save'));
        await waitFor(() => expect(screen.getByText('Please enter a name for the configuration')).toBeInTheDocument());
        fireEvent.click(screen.getByText('Please enter a name for the configuration'));
        await waitFor(() => expect(screen.queryByText('Please enter a name for the configuration')).not.toBeInTheDocument());
    });
});
