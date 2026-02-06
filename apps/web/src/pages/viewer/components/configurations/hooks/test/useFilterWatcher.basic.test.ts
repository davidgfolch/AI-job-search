import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
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
        vi.useRealTimers();
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 10 }, 2: { total: 10, new_items: 10 } });
        const { wrapper, queryClient } = createWrapper();
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

        // First check after start/reset should force newItems to 0
        await waitFor(() => {
            expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
        }, { timeout: 2000 });

        expect(result.current.results['Config 1']).toEqual({ total: 10, newItems: 0 });
        expect(result.current.results['Config 2']).toEqual({ total: 10, newItems: 0 });

        // Trigger another check via query update (does not reset the justReset flag)
        act(() => {
            queryClient.setQueryData(['jobs'], []);
        });

        // Second check should reflect actual values
        await waitFor(() => {
            expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2);
        }, { timeout: 2000 });

        expect(result.current.results['Config 1']).toEqual({ total: 10, newItems: 10 });
        expect(result.current.results['Config 2']).toEqual({ total: 10, newItems: 10 });
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
