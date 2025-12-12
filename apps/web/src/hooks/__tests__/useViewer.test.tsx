import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { jobsApi, type Job } from '../../api/jobs';
import { QueryClient } from '@tanstack/react-query';
import { mockJobs, createWrapper } from './useViewer.fixtures';

// Mock the jobs API
vi.mock('../../api/jobs', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
    },
}));

const setupJobApiMocks = (currentJobs: Job[]) => {
    (jobsApi.getJobs as any).mockImplementation((params: any) => {
        let filtered = [...currentJobs];
        if (params?.seen === false) filtered = filtered.filter(j => !j.seen);
        return Promise.resolve({ items: filtered, total: filtered.length, page: 1, size: 20, pages: 1 });
    });

    (jobsApi.updateJob as any).mockImplementation((id: number, data: Partial<Job>) => {
        const index = currentJobs.findIndex(j => j.id === id);
        if (index !== -1) {
            currentJobs[index] = { ...currentJobs[index], ...data };
            return Promise.resolve(currentJobs[index]);
        }
        return Promise.reject('Not found');
    });

    (jobsApi.getJob as any).mockImplementation((id: number) => {
        const job = currentJobs.find(j => j.id === id);
        return job ? Promise.resolve(job) : Promise.reject('Not found');
    });
};

describe('useViewer', () => {
    let queryClient: QueryClient;
    let currentJobs: Job[];

    beforeEach(() => {
        vi.clearAllMocks();
        currentJobs = JSON.parse(JSON.stringify(mockJobs));
        queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
        setupJobApiMocks(currentJobs);
    });

    const renderViewer = () => renderHook(() => useViewer(), { wrapper: createWrapper(queryClient) });

    it('initializes with default state', async () => {
        const { result } = renderViewer();
        expect(result.current.state.filters).toMatchObject({ page: 1, size: 20, search: '', order: 'created desc' });
        expect(result.current.state.selectedJob).toBeNull();
        expect(result.current.state.allJobs).toEqual([]);
        await waitFor(() => expect(result.current.state.allJobs).toHaveLength(3));
    });

    it('selects a job', async () => {
        const { result } = renderViewer();
        await waitFor(() => expect(result.current.state.allJobs).toHaveLength(3));
        act(() => result.current.actions.selectJob(mockJobs[1]));
        expect(result.current.state.selectedJob?.id).toBe(2);
    });

    it.each([
        { handler: 'seenJob', update: { seen: true } },
        { handler: 'ignoreJob', update: { ignored: true } },
        { handler: 'appliedJob', update: { applied: true } },
        { handler: 'discardedJob', update: { discarded: true } },
        { handler: 'closedJob', update: { closed: true } },
    ])('calls $handler which triggers updateJob with $update', async ({ handler, update }) => {
        const { result } = renderViewer();
        await waitFor(() => expect(result.current.state.allJobs).toHaveLength(3));
        act(() => result.current.actions.selectJob(mockJobs[0]));
        await act(async () => (result.current.actions as any)[handler]()); // generic call
        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, update);
    });

    it('handles auto-selection logic properly', async () => {
        const { result } = renderViewer();
        await waitFor(() => expect(result.current.state.allJobs).toHaveLength(3));
        // Filter out seen jobs
        act(() => result.current.actions.setFilters((prev) => ({ ...prev, seen: false })));
        await waitFor(() => expect(result.current.state.filters.seen).toBe(false));
        // LIST mode: should auto-select next
        act(() => result.current.actions.selectJob(mockJobs[0])); // Job 1
        await act(async () => result.current.actions.seenJob());
        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { seen: true });
        await waitFor(() => expect(result.current.state.selectedJob?.id).toBe(2)); // Auto-selected Job 2
        // EDIT mode: should NOT auto-select
        act(() => result.current.actions.setActiveTab('edit'));
        await act(async () => result.current.actions.seenJob()); // This will mark Job 2 as seen
        expect(jobsApi.updateJob).toHaveBeenCalledWith(2, { seen: true });
        // Wait to ensure NO auto-select happens
        await new Promise(r => setTimeout(r, 100));
        expect(result.current.state.selectedJob?.id).toBe(2); // Should remain Job 2
    });

    it.each([
        { action: 'nextJob', startId: 2, expectedId: 3 },
        { action: 'previousJob', startId: 2, expectedId: 1 },
    ])('navigation $action moves from $startId to $expectedId', async ({ action, startId, expectedId }) => {
        const { result } = renderViewer();
        await waitFor(() => expect(result.current.state.allJobs).toHaveLength(3));
        act(() => result.current.actions.selectJob(mockJobs.find(j => j.id === startId)!));
        act(() => (result.current.actions as any)[action]());
        expect(result.current.state.selectedJob?.id).toBe(expectedId);
    });

    it('generic handleJobUpdate calls API', async () => {
        const { result } = renderViewer();
        await waitFor(() => expect(result.current.state.allJobs).toHaveLength(3));
        act(() => result.current.actions.selectJob(mockJobs[0]));
        await act(async () => result.current.actions.updateJob({ comments: 'New Comment' }));
        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { comments: 'New Comment' });
    });
});
