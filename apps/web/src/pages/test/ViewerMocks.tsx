import { vi, beforeEach, afterEach } from 'vitest';
import { act } from '@testing-library/react';

export const runTimers = async () => {
    await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
    });
};

export const MockJobList = ({ jobs, onJobSelect, onLoadMore, isLoading, error }: any) => {
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
};

export const MockJobDetail = ({ job }: any) => (
    <div>
        <div className="markdown-content"><p>{job.markdown}</p></div>
        <div>{job.company}</div>
        <div>{job.company}</div>
        <div>already applied</div>
    </div>
);

export const MockFilters = ({ onConfigNameChange, onFiltersChange }: any) => (
    <div>
        <button onClick={() => onFiltersChange({ flagged: true })}>Flagged</button>
        <button>Filters</button>
        <button>Save</button>
        <div onClick={() => onConfigNameChange('test')}>Please enter a name for the configuration</div>
    </div>
);

export const MockViewTabs = ({ onTabChange, onReload }: any) => (
    <div>
        <button onClick={() => onTabChange('list')}>List</button>
        <button onClick={() => onTabChange('edit')}>Edit</button>
        <button onClick={onReload}>new</button>
    </div>
);

export const MockJobEditForm = ({ mode }: any) => (
    <div>
        <label>{mode === 'create' ? 'Create Comments' : 'Edit Comments'}</label>
    </div>
);

export const MockJobActions = () => null;

export const MockReactMarkdownCustom = ({ children }: { children: React.ReactNode }) => <p>{children}</p>;

export const setupGlobalMocks = () => {
    globalThis.IntersectionObserver = vi.fn(function(this: any) {
        return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
    }) as any;
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
