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

describe('useFilterWatcher - Polling Logic', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        cleanupMocks();
    });

    it.skip('should poll periodically', async () => {
        vi.useFakeTimers();
        (jobsApi.countJobs as any).mockResolvedValue(5);
        
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }));

        await act(async () => {
            result.current.startWatching();
        });

        expect(jobsApi.countJobs).toHaveBeenCalledTimes(2);

        await act(async () => {
            vi.advanceTimersByTime(5 * 60 * 1000);
        });

        expect(jobsApi.countJobs).toHaveBeenCalledTimes(4);
    });
    
    it('should pass created_after parameter when checking new items', async () => {
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }));
         
         (jobsApi.countJobs as any).mockResolvedValue(5);

         act(() => {
             result.current.startWatching();
         });

         await waitFor(() => {
             expect(jobsApi.countJobs).toHaveBeenCalled();
         });
         
         const calls = (jobsApi.countJobs as any).mock.calls;
         const newItemsCallParams = calls[1][0];
         expect(newItemsCallParams).toHaveProperty('created_after');
         expect(typeof newItemsCallParams.created_after).toBe('string');
    });

    it('should reset watcher for a config without triggering immediate check', async () => {
         (jobsApi.countJobs as any).mockResolvedValue(10);
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }));

         await act(async () => {
             result.current.startWatching();
         });

         await waitFor(() => {
             expect(jobsApi.countJobs).toHaveBeenCalledTimes(4);
         });

         (jobsApi.countJobs as any).mockClear();

         act(() => {
             result.current.resetWatcher('Config 1');
         });

         expect(result.current.results['Config 1'].newItems).toBe(0);
         expect(jobsApi.countJobs).not.toHaveBeenCalled();
    });
});
