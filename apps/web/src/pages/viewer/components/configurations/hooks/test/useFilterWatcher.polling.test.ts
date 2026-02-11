import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher, POLLING_INTERVAL } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { mockSavedConfigs, cleanupMocks, createWrapper } from './testHelpers';

vi.mock('../../../../api/ViewerApi', () => ({
    jobsApi: {
        getWatcherStats: vi.fn(),
        getSystemTimezone: vi.fn().mockResolvedValue({ offset_minutes: 0 })
    }
}));

vi.mock('../../../../../../common/services/NotificationService', () => ({
    notificationService: {
        requestPermission: vi.fn(),
        watched: vi.fn(),
        hasPermission: vi.fn().mockReturnValue(true)
    }
}));

describe('useFilterWatcher - Polling Logic', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        cleanupMocks();
    });

    it('should poll periodically', async () => {
        vi.useFakeTimers();
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 5 } });
        
        const { wrapper, queryClient } = createWrapper();
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }), { wrapper });

        // Handle initial check on mount. Since it's debounced by 200ms,
        // we need to advance the timers.
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });

        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
        // First check after reset/mount should be 0
        expect(Object.values(result.current.results)[0].newItems).toBe(0);

        // Catch up check: server reports 0 for the future cutoff
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 0 } });
        await act(async () => {
             await vi.advanceTimersByTimeAsync(1000); // Trigger another debounced check if we can, or just wait for next poll
             // Wait, query update is the easiest way to trigger in this test environment
             queryClient.setQueryData(['jobs'], []);
             await vi.advanceTimersByTimeAsync(200);
        });
        expect(Object.values(result.current.results)[0].newItems).toBe(0);

        vi.clearAllMocks();

        // Periodic poll: now server reports 5 new items since the catch-up
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 5 } });
        await act(async () => {
            await vi.advanceTimersByTimeAsync(POLLING_INTERVAL);
        });

        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2);
        expect(Object.values(result.current.results)[0].newItems).toBe(5);
    });
    
    it('should pass created_after parameter when checking new items', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 5 } });
         const { wrapper } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }), { wrapper });
         
         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });
         
         const calls = (jobsApi.getWatcherStats as any).mock.calls;
         const cutoffMapArg = calls[calls.length - 1][0];
         expect(cutoffMapArg).toBeDefined();
         expect(typeof cutoffMapArg).toBe('object');
         expect(cutoffMapArg[1]).toBeDefined();
         expect(typeof cutoffMapArg[1]).toBe('string');
    });

    it('should reset watcher for a config without triggering immediate check', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 10 }, 2: { total: 10, new_items: 10 } });
          const { wrapper } = createWrapper();
          const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });

         (jobsApi.getWatcherStats as any).mockClear();

         act(() => {
             result.current.resetWatcher('Config 1');
         });

         expect(result.current.results['Config 1'].newItems).toBe(0);
         expect(jobsApi.getWatcherStats).not.toHaveBeenCalled();
    });
});
