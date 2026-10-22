import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
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

describe('useFilterWatcher - Basic Functionality', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        cleanupMocks();
    });

    it('should initialize with watching state', async () => {
        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });
        await waitFor(() => {
            expect(result.current.isWatching).toBe(true);
        });
        expect(result.current.results).toEqual({});
    });

    it('should start watching and trigger immediate check', async () => {
        vi.useFakeTimers();
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 10 }, 2: { total: 10, new_items: 10 } });
        const { wrapper, queryClient } = createWrapper();
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

        // Initial check is debounced by 200ms
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });

        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
        // The count reported by the backend is shown as-is: the cutoff already
        // expresses "seen up to now", so nothing may be masked out.
        expect(result.current.results['Config 1']).toEqual({ total: 10, newItems: 10, removedItems: 0 });
        expect(result.current.results['Config 2']).toEqual({ total: 10, newItems: 10, removedItems: 0 });

        // Second check: server still reports 10 (simulating clock skew or lag)
        act(() => {
            queryClient.setQueryData(['jobs'], []);
        });
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });
        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2);
        expect(result.current.results['Config 1'].newItems).toBe(10);

        // Third check: server finally reports 0 (catches up)
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 0 }, 2: { total: 10, new_items: 0 } });
        act(() => {
            queryClient.setQueryData(['jobs'], []);
        });
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });
        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(3);
        expect(result.current.results['Config 1'].newItems).toBe(0);

        // Fourth check: new items arrive AFTER server caught up
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 11, new_items: 1 }, 2: { total: 11, new_items: 1 } });
        act(() => {
            queryClient.setQueryData(['jobs'], []);
        });
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });
        expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(4);
        expect(result.current.results['Config 1'].newItems).toBe(1);
    });

    it('should send an independent cutoff per configuration after a reset', async () => {
        vi.useFakeTimers();
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 0 }, 2: { total: 5, new_items: 0 } });
        const { wrapper, queryClient } = createWrapper();
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });
        const calls = (jobsApi.getWatcherStats as any).mock.calls;
        const firstCutoffMap = calls[0][0];
        expect(firstCutoffMap[1]).toEqual(firstCutoffMap[2]);

        // Reloading one configuration moves only its own cutoff forward.
        act(() => {
            result.current.resetWatcher('Config 1');
        });
        act(() => {
            queryClient.setQueryData(['jobs'], []);
        });
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });

        const allCalls = (jobsApi.getWatcherStats as any).mock.calls;
        const lastCutoffMap = allCalls[allCalls.length - 1][0];
        expect(lastCutoffMap[1]).not.toEqual(lastCutoffMap[2]);
    });

    it('should stop watching', async () => {
        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

        // Already watching on mount
        await waitFor(() => {
            expect(jobsApi.getWatcherStats).toHaveBeenCalled();
        });

        expect(result.current.isWatching).toBe(true);

        act(() => {
            result.current.stopWatching();
        });
        expect(result.current.isWatching).toBe(false);
    });
});
