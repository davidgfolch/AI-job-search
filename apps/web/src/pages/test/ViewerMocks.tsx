import { vi, beforeEach, afterEach } from 'vitest';
import { act } from '@testing-library/react';
import type { Job } from '../viewer/api/ViewerApi';

export const runTimers = async () => {
    await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
    });
};

export const MockJobList = ({ jobs, onJobSelect, onLoadMore, isLoading, error }: { jobs: Job[]; onJobSelect: (job: Job) => void; onLoadMore: () => void; isLoading: boolean; error: Error | null }) => {
    if (isLoading) return <div>Loading jobs...</div>;
    if (error) return <div>{error.message}</div>;
    return (
        <div>
            {jobs.map((job) => (
                <div key={job.id} role="cell" aria-label={job.title ?? undefined} onClick={() => onJobSelect(job)}>
                    {job.title}
                </div>
            ))}
            <button onClick={onLoadMore}>Load More</button>
        </div>
    );
};

export const MockSelectableJobList = ({ jobs, onToggleSelectJob, onToggleSelectAll }: { jobs: Job[]; onToggleSelectJob: (id: number) => void; onToggleSelectAll: () => void }) => (
    <div>
        <input id="job-table-select-all" type="checkbox" onChange={onToggleSelectAll} />
        {jobs.map((job) => (
            <div key={job.id}>
                <input
                    id={`job-job-${job.id}-checkbox`}
                    type="checkbox"
                    aria-label={`Select ${job.title}`}
                    onChange={() => onToggleSelectJob(job.id)}
                />
                <span>{job.title}</span>
            </div>
        ))}
    </div>
);

export const MockJobDetail = ({ job }: { job: Job }) => (
    <div>
        <div className="markdown-content"><p>{job.markdown}</p></div>
        <div>{job.company}</div>
        <div>{job.company}</div>
        <div>already applied</div>
    </div>
);

export const MockFilters = ({ onConfigNameChange, onFiltersChange }: { onConfigNameChange: (name: string) => void; onFiltersChange: (filters: { flagged: boolean }) => void }) => (
    <div>
        <button onClick={() => onFiltersChange({ flagged: true })}>Flagged</button>
        <button>Filters</button>
        <button>Save</button>
        <div onClick={() => onConfigNameChange('test')}>Please enter a name for the configuration</div>
    </div>
);

export const MockViewTabs = ({ onTabChange, onReload }: { onTabChange: (tab: string) => void; onReload: () => void }) => (
    <div>
        <button onClick={() => onTabChange('list')}>List</button>
        <button onClick={() => onTabChange('edit')}>Edit</button>
        <button onClick={onReload}>new</button>
    </div>
);

export const MockJobEditForm = ({ mode }: { mode: string }) => (
    <div>
        <label>{mode === 'create' ? 'Create Comments' : 'Edit Comments'}</label>
    </div>
);

export const MockJobActions = () => null;

export const MockReactMarkdownCustom = ({ children }: { children: React.ReactNode }) => <p>{children}</p>;

export const setupGlobalMocks = () => {
    globalThis.IntersectionObserver = vi.fn(() => ({
        observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn()
    })) as unknown as typeof IntersectionObserver;
};

export const setupTestLifecycle = () => {
    beforeEach(() => { 
        vi.useFakeTimers();
        vi.clearAllMocks(); 
    });
    afterEach(() => {
        vi.useRealTimers();
    });
};
