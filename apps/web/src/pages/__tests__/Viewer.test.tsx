import { screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { jobsApi } from '../../api/jobs';
import { mockJobs, renderViewer } from './ViewerTestUtils';
import { mockJobsApiDefault, selectJob, switchToTab, clickFilterButton, verifySummary } from './ViewerTestHelpers';

// --- Local Helpers ---
const runTimers = async () => {
    await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
    });
};

// --- Mocks ---
vi.mock('../../components/JobList', () => ({
    default: ({ jobs, onJobSelect, onLoadMore, isLoading, error }: any) => {
        if (isLoading) return <div>Loading jobs...</div>;
        if (error) return <div>{error.message}</div>;
        return (
            <div>
                {jobs.map((job: any) => (
                    <div key={job.id} role="cell" aria-label={job.title} onClick={() => onJobSelect(job)}>
                        {job.title}
                    </div>
                ))}
                <button onClick={onLoadMore}>Load More</button>
            </div>
        );
    }
}));

// ... (keep other mocks same, skipping for brevity in instructions but tool handles it)



vi.mock('../../components/JobDetail', () => ({
    default: ({ job }: any) => (
        <div>
            <div className="markdown-content"><p>{job.markdown}</p></div>
            <div>{job.company}</div>
            <div>{job.company}</div>
            <div>already applied</div>
        </div>
    )
}));

vi.mock('../../components/Filters', () => ({
    default: ({ onConfigNameChange, onFiltersChange }: any) => (
        <div>
            <button onClick={() => onFiltersChange({ flagged: true })}>Flagged</button>
            <button>Filters</button>
            <button>Save</button>
            <div onClick={() => onConfigNameChange('test')}>Please enter a name for the configuration</div>
        </div>
    )
}));

vi.mock('../../components/ViewTabs', () => ({
    default: ({ onTabChange, onReload }: any) => (
        <div>
            <button onClick={() => onTabChange('list')}>List</button>
            <button onClick={() => onTabChange('edit')}>Edit</button>
            <button onClick={onReload}>new</button>
        </div>
    )
}));

vi.mock('../../components/JobEditForm', () => ({
    default: ({ mode }: any) => (
        <div>
            <label>{mode === 'create' ? 'Create Comments' : 'Edit Comments'}</label>
        </div>
    )
}));

vi.mock('../../components/JobActions', () => ({
    default: () => null
}));

globalThis.IntersectionObserver = vi.fn(function(this: any) {
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

vi.mock('../../components/core/ReactMarkdownCustom', () => ({
    default: ({ children }: { children: React.ReactNode }) => <p>{children}</p>
}));

vi.mock('../../services/FilterConfigService', () => {
    return {
        FilterConfigService: vi.fn().mockImplementation(function() {
            return {
                load: vi.fn().mockResolvedValue([]),
                save: vi.fn().mockResolvedValue(undefined),
                delete: vi.fn().mockResolvedValue(undefined),
                export: vi.fn().mockResolvedValue([])
            };
        })
    };
});

// --- Tests ---
describe('Viewer', () => {
    beforeEach(() => { 
        vi.useFakeTimers();
        vi.clearAllMocks(); 
    });

    afterEach(() => {
        vi.useRealTimers();
    });
    
    const stateTestCases = [
        {
            name: 'renders loading state initially',
            mockSetup: () => (jobsApi.getJobs as any).mockReturnValue(new Promise(() => { })),
            assertion: async () => {
                expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
                await runTimers();
            }
        },
        {
            name: 'renders job list after loading',
            mockSetup: () => (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 }),
            assertion: async () => {
                await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
                verifySummary(/2\/2 loaded \| 0 Selected/);
            }
        },
        {
            name: 'handles error state',
            mockSetup: () => (jobsApi.getJobs as any).mockRejectedValue(new Error('Failed to fetch')),
            assertion: async () => {
                await runTimers();
                expect(screen.getAllByText('Failed to fetch').length).toBeGreaterThan(0);
            }
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
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
        selectJob('Job 1');
        await runTimers();
        expect(screen.getByText('Description 1', { selector: '.markdown-content p' })).toBeInTheDocument();
        expect(screen.getAllByText('Company 1')).toHaveLength(2);
        clickFilterButton('Flagged');
        
        expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ flagged: true, page: 1 }));
        await runTimers();
    });

    it('handles tab switching and edit interactions', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        selectJob('Job 1');
        switchToTab('Edit');
        expect(screen.getByText('Edit Comments')).toBeInTheDocument();
        switchToTab('List');
        expect(screen.getByRole('cell', { name: 'Job 1' })).toBeInTheDocument();
        await runTimers();
    });

    it('handles infinite scroll', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 50, page: 1, size: 20 });
        renderViewer();
        await runTimers();
        verifySummary(/2\/50 loaded \| 0 Selected/);
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(1);
    });



    it('filters by URL ids', async () => {
        mockJobsApiDefault();
        renderViewer(['/?ids=1,2']);
        await runTimers();
        expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ sql_filter: 'id IN (1,2)', page: 1 }));
    });

    it('refreshes list when clicking List tab if new jobs exist', async () => {
        const { useJobUpdates } = await import('../../hooks/viewer/useJobUpdates');
        (useJobUpdates as any).mockReturnValue({ hasNewJobs: true, newJobsCount: 5 });
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        selectJob('Job 1');
        switchToTab('Edit');
        expect(screen.getByText('Edit Comments')).toBeInTheDocument();
        (jobsApi.getJobs as any).mockClear();
        const reloadBtn = screen.getByText((content, element) => element?.tagName.toLowerCase() === 'button' && content.includes('new'));
        fireEvent.click(reloadBtn);
        // hardRefresh calls queryClient.resetQueries which triggers a refetch that ultimately calls jobsApi.getJobs
        await runTimers();
        expect(jobsApi.getJobs).toHaveBeenCalled();
    });





    it('loads job details when clicking a job loaded via infinite scroll', async () => {
        vi.useFakeTimers();
        (jobsApi.getJobs as any).mockResolvedValueOnce({ items: mockJobs, total: 4, page: 1, size: 2 });
        const page2Jobs = [
            { id: 3, title: 'Job 3', company: 'Company 3', description: 'Desc 3', date: '2024-01-02', markdown: 'Desc 3', created: '2024-01-02' },
            { id: 4, title: 'Job 4', company: 'Company 4', description: 'Desc 4', date: '2024-01-02', markdown: 'Desc 4', created: '2024-01-02' }
        ];
        (jobsApi.getJobs as any).mockResolvedValueOnce({ items: page2Jobs, total: 4, page: 2, size: 2 });
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([]);
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        
        fireEvent.click(screen.getByText('Load More'));
        await runTimers();

        expect(screen.getByText('Job 3')).toBeInTheDocument();
        selectJob('Job 3');
        await runTimers();
        expect(screen.getByText('Desc 3', { selector: '.markdown-content p' })).toBeInTheDocument();
    });
});
