import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFilterWatcher, LAST_WATCHER_CHECK_TIME_KEY } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { persistenceApi } from '../../../../../../pages/common/api/CommonPersistenceApi';
import { mockSavedConfigs, createWrapper } from './testHelpers';

vi.mock('../../../../api/ViewerApi', () => ({
    jobsApi: {
        getWatcherStats: vi.fn(),
        getSystemTimezone: vi.fn().mockResolvedValue({ offset_minutes: 0 })
    }
}));

vi.mock('../../../../../../pages/common/api/CommonPersistenceApi', () => ({
    persistenceApi: {
        getValue: vi.fn(),
        setValue: vi.fn().mockResolvedValue(undefined)
    }
}));

describe('useFilterWatcher - Persistence', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should initialize startTime and lastCheckTime from localStorage', async () => {
        const persistedTime = '2026-02-08T08:00:00.000Z';
        (persistenceApi.getValue as any).mockResolvedValue(persistedTime);
        const { wrapper } = createWrapper();

        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

        await waitFor(() => {
            expect(result.current.lastCheckTime?.toISOString()).toBe(persistedTime);
        });
        expect(persistenceApi.getValue).toHaveBeenCalledWith(LAST_WATCHER_CHECK_TIME_KEY);
    });

    it('should update localStorage after a successful checkItems', async () => {
        vi.useFakeTimers();
        (persistenceApi.getValue as any).mockResolvedValue(null);
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 0 } });
        const { wrapper } = createWrapper();

        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper });

        // Trigger checkItems via debounce
        await act(async () => {
            await vi.advanceTimersByTimeAsync(200);
        });

        expect(jobsApi.getWatcherStats).toHaveBeenCalled();
        expect(persistenceApi.setValue).toHaveBeenCalledWith(
            LAST_WATCHER_CHECK_TIME_KEY,
            expect.any(String)
        );
        
        const lastCall = (persistenceApi.setValue as any).mock.calls[0];
        expect(new Date(lastCall[1]).getTime()).toBeGreaterThan(0);

        vi.useRealTimers();
    });
});
