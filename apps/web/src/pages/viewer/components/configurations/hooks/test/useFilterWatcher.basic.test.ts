import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { mockSavedConfigs, cleanupMocks } from './testHelpers';

vi.mock('../../../../api/ViewerApi', () => ({
    jobsApi: {
        countJobs: vi.fn()
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

    it('should initialize with not watching state', () => {
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }));
        expect(result.current.isWatching).toBe(false);
        expect(result.current.results).toEqual({});
    });

    it('should start watching and trigger immediate check', async () => {
        (jobsApi.countJobs as any).mockResolvedValue(10);
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }));

        act(() => {
            result.current.startWatching();
        });

        expect(result.current.isWatching).toBe(true);

        await waitFor(() => {
            expect(jobsApi.countJobs).toHaveBeenCalledTimes(4);
        });
        
        expect(Object.keys(result.current.results)).toHaveLength(2);
        expect(result.current.results['Config 1']).toEqual({ total: 10, newItems: 10 });
        expect(result.current.results['Config 2']).toEqual({ total: 10, newItems: 10 });
    });

    it('should stop watching', async () => {
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }));

        await act(async () => {
            result.current.startWatching();
        });
        
        await waitFor(() => {
            expect(jobsApi.countJobs).toHaveBeenCalled();
        });

        expect(result.current.isWatching).toBe(true);

        act(() => {
            result.current.stopWatching();
        });
        expect(result.current.isWatching).toBe(false);
    });
});
