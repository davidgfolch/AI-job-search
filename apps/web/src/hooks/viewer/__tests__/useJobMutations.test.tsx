import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobMutations } from '../useJobMutations';
import { jobsApi } from '../../../api/jobs';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock jobsApi
vi.mock('../../../api/jobs', () => ({
    jobsApi: {
        updateJob: vi.fn(),
        bulkUpdateJobs: vi.fn(),
    },
}));

// Setup QueryClient wrapper
const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useJobMutations', () => {
    const defaultProps = {
        filters: {},
        selectedJob: { id: 1, title: 'Job 1', ignored: false } as any,
        setSelectedJob: vi.fn(),
        activeTab: 'list' as const,
        autoSelectNext: { current: { shouldSelect: false, previousJobId: null } },
        selectedIds: new Set<number>(),
        setSelectedIds: vi.fn(),
        selectionMode: 'none' as const,
        setSelectionMode: vi.fn(),
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should initialize with default state', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        expect(result.current.message).toBeNull();
        expect(result.current.confirmModal.isOpen).toBe(false);
    });

    it('should handle single job update success', async () => {
        (jobsApi.updateJob as any).mockResolvedValue({ id: 1, title: 'Job 1 Updated', ignored: false });

        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });

        await act(async () => {
            result.current.updateMutation.mutate({ id: 1, data: { title: 'New Title' } });
        });

        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { title: 'New Title' });
        expect(defaultProps.setSelectedJob).toHaveBeenCalledWith({ id: 1, title: 'Job 1 Updated', ignored: false });
    });

    it('should handle autoSelectNext when state field is updated in list mode', async () => {
        (jobsApi.updateJob as any).mockResolvedValue({ id: 1, ignored: true });

        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });

        await act(async () => {
             // 'ignored' is a state field that triggers auto-select
            result.current.handleJobUpdate({ ignored: true });
        });

        expect(defaultProps.autoSelectNext.current).toEqual({ shouldSelect: true, previousJobId: 1 });
        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { ignored: true });
    });

    it('should NOT handle autoSelectNext when non-state field is updated', async () => {
        (jobsApi.updateJob as any).mockResolvedValue({ id: 1, title: 'Updated' });
        // Reset ref
        defaultProps.autoSelectNext.current = { shouldSelect: false, previousJobId: null };

        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });

        await act(async () => {
            result.current.handleJobUpdate({ title: 'New Title' } as any);
        });

        expect(defaultProps.autoSelectNext.current.shouldSelect).toBe(false);
    });

    it('should handle bulk update success', async () => {
        (jobsApi.bulkUpdateJobs as any).mockResolvedValue({ updated: 5 });

        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });

        await act(async () => {
            result.current.bulkUpdateMutation.mutate({ ids: [1, 2, 3], update: { ignored: true } });
        });

        expect(jobsApi.bulkUpdateJobs).toHaveBeenCalled();
        expect(result.current.message).toEqual({ text: 'Updated 5 jobs', type: 'success' });
        expect(defaultProps.setSelectionMode).toHaveBeenCalledWith('none');
        expect(defaultProps.setSelectedIds).toHaveBeenCalledWith(new Set());
    });

    it('should open confirmation modal for ignoreSelected', async () => {
        // Simulate selection
        const props = { ...defaultProps, selectedIds: new Set([1, 2]), selectionMode: 'manual' as const };
        
        const { result } = renderHook(() => useJobMutations(props), { wrapper: createWrapper() });

        act(() => {
            result.current.ignoreSelected();
        });

        expect(result.current.confirmModal.isOpen).toBe(true);
        expect(result.current.confirmModal.message).toContain('ignore 2 selected jobs');
    });
    
    it('should execute bulk ignore on confirmation', async () => {
        (jobsApi.bulkUpdateJobs as any).mockResolvedValue({ updated: 2 });
         const props = { ...defaultProps, selectedIds: new Set([1, 2]), selectionMode: 'manual' as const };
        
        const { result } = renderHook(() => useJobMutations(props), { wrapper: createWrapper() });

        act(() => {
            result.current.ignoreSelected();
        });
        
        // Confirm
        await act(async () => {
            result.current.confirmModal.onConfirm();
        });

        expect(jobsApi.bulkUpdateJobs).toHaveBeenCalledWith(expect.objectContaining({
             ids: [1, 2],
             update: { ignored: true }
        }));
        expect(result.current.confirmModal.isOpen).toBe(false);
    });
});
