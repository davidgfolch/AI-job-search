import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { createTestQueryClient } from '../../test/test-utils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { jobsApi } from '../../api/ViewerApi';
import { MemoryRouter } from 'react-router-dom';

// Mock the jobs API
vi.mock('../../api/ViewerApi', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        updateJob: vi.fn(),
        createJob: vi.fn(),
    }
}));

const createWrapper = () => {
    const queryClient = createTestQueryClient();
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
             <MemoryRouter>
                {children}
            </MemoryRouter>
        </QueryClientProvider>
    );
};

describe('useViewer - Flicker Reproduction', () => {
    let mockJobs: any[];

    beforeEach(() => {
        mockJobs = [
            { id: 1, title: 'Job 1', ignored: false },
            { id: 2, title: 'Job 2', ignored: false },
             { id: 3, title: 'Job 3', ignored: false }
        ];
        vi.clearAllMocks();
        
        // Dynamic behavior for getJobs
        (jobsApi.getJobs as any).mockImplementation((params: any) => {
            const list = mockJobs.filter(j => !j.ignored);
            return Promise.resolve({
                items: list,
                total: list.length,
                page: 1,
                size: 10,
                pages: 1
            });
        });

        (jobsApi.updateJob as any).mockImplementation((id: number, data: any) => {
            const job = mockJobs.find(j => j.id === id);
            if (job) Object.assign(job, data);
            return Promise.resolve(job);
        });
    });

    it('should NOT show new jobs button after ignoring a job', async () => {
        const { result } = renderHook(() => useViewer(), {
            wrapper: createWrapper()
        });

        // 1. Initial Load
        await waitFor(() => expect(result.current.state.allJobs.length).toBe(3));
        expect(result.current.state.hasNewJobs).toBe(false);

        // 2. Select first job
        act(() => {
            result.current.actions.selectJob(result.current.state.allJobs[0]);
        });

        // 3. Ignore selected job
        await act(async () => {
             result.current.actions.ignoreJob();
        });
        
        // Wait for update
        await waitFor(() => expect(result.current.state.allJobs.length).toBe(2));

        // 4. Verify "New Jobs" does NOT appear
        // The flicker happens because getJobs returns 2 items (ids 2,3)
        // usageJobUpdates (background) might accidentally fetch [2,3] and compare?
        // Or if the query wasn't invalidated, it might still have old [1,2,3]?
        // IF we don't invalidate jobUpdates, it holds [1,2,3].
        // knownJobIds holds [1,2,3].
        // So actually, if jobUpdates is stale, it has MORE items than needed -> no new jobs.
        
        // BUT, what if the background query runs and returns [2,3] (server state)?
        // knownJobIds has [1,2,3].
        // [2,3] filter !has -> empty.
        
        // Wait, where is the flicker coming from?
        // Maybe "new jobs" logic is finding something else?
        
        expect(result.current.state.hasNewJobs).toBe(false);
    });
});
