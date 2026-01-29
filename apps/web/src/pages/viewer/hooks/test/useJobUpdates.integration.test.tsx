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

describe('useViewer - "New Jobs" bug reproduction', () => {
    let mockJobs: any[];

    beforeEach(() => {
        mockJobs = [
            { id: 1, title: 'Job 1', discarded: false },
            { id: 2, title: 'Job 2', discarded: false }
        ];
        vi.clearAllMocks();
        
        // Mock getJobs to behave dynamically:
        // If "discarded=false" (default), filter out discarded jobs from mockJobs
        // For simplicity, we just check the global mockJobs array state which we will update
        (jobsApi.getJobs as any).mockImplementation(() => {
            const filtered = mockJobs.filter(j => !j.discarded);
            return Promise.resolve({
                items: filtered,
                total: filtered.length,
                page: 1,
                size: 10,
                pages: 1
            });
        });

        (jobsApi.updateJob as any).mockImplementation((id: number, data: any) => {
            const job = mockJobs.find(j => j.id === id);
            if (job) {
                Object.assign(job, data);
            }
            return Promise.resolve(job);
        });
    });

    it('should NOT count discarded jobs as "new" jobs', async () => {
        const { result } = renderHook(() => useViewer(), {
            wrapper: createWrapper()
        });

        // Wait for initial load
        await waitFor(() => expect(result.current.state.allJobs.length).toBe(2));

        // Initial state: 2 jobs loaded, 0 new jobs
        expect(result.current.state.newJobsCount).toBe(0);
        expect(result.current.state.hasNewJobs).toBe(false);

        // Simulate discarding a job (local state update)
        // This removes it from 'allJobs' in the current filter view
        act(() => {
            result.current.actions.discardedJob(); // Will discard the selected job
        });

        // But first we need to select a job to discard
         act(() => {
            result.current.actions.selectJob(mockJobs[0] as any);
        });

        act(() => {
            result.current.actions.discardedJob();
        });

         // Wait for the job to be removed from the list
        await waitFor(() => expect(result.current.state.allJobs.length).toBe(1));

        // The background update query (useJobUpdates) will still fetch the original 2 jobs from the server
        // because we haven't actually updated the server mock to reflect the discard in the list endpoint
        // (and even if we did, the bug is about *local* removal vs background fetch logic)
        
        // BUG EXPECTATION:
        // 'useJobUpdates' sees 2 jobs from server.
        // 'useViewer' has 1 job in 'allJobs' (the other was discarded locally).
        // The logic `data.items.filter(job => !allJobIds.has(job.id))` will find the discarded job ID returned by server
        // but NOT present in 'allJobs', so it counts it as "new".
        
        // We expect this to FAIL once the bug is fixed.
        // For reproduction, we assert the current buggy behavior (or asserted the "correct" behavior and expect test failure).
        // Let's assert the CORRECT behavior so the test fails now and passes later.
        
        expect(result.current.state.newJobsCount).toBe(0);
        expect(result.current.state.hasNewJobs).toBe(false);
    });
});
