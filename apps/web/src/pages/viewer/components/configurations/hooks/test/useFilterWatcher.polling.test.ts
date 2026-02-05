import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher, POLLING_INTERVAL } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { mockSavedConfigs, cleanupMocks, createWrapper } from './testHelpers';

vi.mock('../../../../api/ViewerApi', () => ({
    jobsApi: {
        getWatcherStats: vi.fn()
    }
}));

vi.mock('../../../../../../common/services/NotificationService', () => ({
    notificationService: {
        requestPermission: vi.fn(),
        notify: vi.fn(),
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
        
        renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }), { wrapper: createWrapper() });

        // Handle initial check on mount. Since it's async but triggered immediately, 
        // a zero-time advance helps flush microtasks in Vitest's fake timer environment.
        await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
        });

        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
        vi.clearAllMocks();

        // Periodic poll
        await act(async () => {
            await vi.advanceTimersByTimeAsync(POLLING_INTERVAL);
        });

        // 1 call for one config (total and new)
        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
    });
    
    it('should pass created_after parameter when checking new items', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 5 } });
         renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }), { wrapper: createWrapper() });
         
         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });
         
         const calls = (jobsApi.getWatcherStats as any).mock.calls;
         const configIdsArg = calls[0][0];
         const watcherCutoffArg = calls[0][1];
         expect(configIdsArg).toEqual([1]);
         expect(watcherCutoffArg).toBeDefined();
         expect(typeof watcherCutoffArg).toBe('string');
    });

    it('should reset watcher for a config without triggering immediate check', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 10 }, 2: { total: 10, new_items: 10 } });
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper: createWrapper() });

         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
         });

         (jobsApi.getWatcherStats as any).mockClear();

         act(() => {
             result.current.resetWatcher('Config 1');
         });

         expect(result.current.results['Config 1'].newItems).toBe(0);
         expect(jobsApi.getWatcherStats).not.toHaveBeenCalled();
    });
});
