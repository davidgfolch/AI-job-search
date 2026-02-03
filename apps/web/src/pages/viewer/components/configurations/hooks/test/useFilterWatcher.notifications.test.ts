import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { notificationService } from '../../../../../../common/services/NotificationService';
import { mockSavedConfigs, cleanupMocks } from './testHelpers';

vi.mock('../../../../api/ViewerApi', () => ({
    jobsApi: {
        getJobs: vi.fn()
    }
}));

vi.mock('../../../../../../common/services/NotificationService', () => ({
    notificationService: {
        requestPermission: vi.fn(),
        notify: vi.fn(),
        hasPermission: vi.fn().mockReturnValue(true)
    }
}));

describe('useFilterWatcher - Notifications', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mock implementation to prevent undefined errors
        (jobsApi.getJobs as any).mockResolvedValue({ total: 0, items: [] });
    });

    afterEach(() => {
        cleanupMocks();
    });

    it('should request notification permission when starting watch', async () => {
        const { result } = renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }));
        
        act(() => {
            result.current.startWatching();
        });

        await waitFor(() => {
            expect(notificationService.requestPermission).toHaveBeenCalled();
        });
    });

    it('should trigger aggregated notification for enabled configs', async () => {
         (jobsApi.getJobs as any).mockResolvedValue({ total: 5, items: [] });
         
         const config1 = { ...mockSavedConfigs[0], notify: true };
         const config2 = { ...mockSavedConfigs[1], notify: true };
         
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [config1, config2] }));

         await act(async () => {
             result.current.startWatching();
         });

         await waitFor(() => {
             expect(jobsApi.getJobs).toHaveBeenCalledTimes(4);
         });

         expect(notificationService.notify).toHaveBeenCalledWith(
             expect.stringContaining('New jobs found'),
             expect.objectContaining({ 
                 body: expect.stringMatching(/Config 1 \(5\)/) 
             })
         );
         expect(notificationService.notify).toHaveBeenCalledWith(
             expect.stringContaining('New jobs found'),
             expect.objectContaining({ 
                 body: expect.stringMatching(/Config 2 \(5\)/) 
             })
         );
    });

    it('should NOT trigger notification for disabled configs', async () => {
         (jobsApi.getJobs as any).mockResolvedValue({ total: 5, items: [] });
         
         const config1 = { ...mockSavedConfigs[0], notify: false };
         
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [config1] }));

         await act(async () => {
             result.current.startWatching();
         });

         await waitFor(() => {
             expect(jobsApi.getJobs).toHaveBeenCalled();
         });

         expect(notificationService.notify).not.toHaveBeenCalled();
    });

    it('should NOT trigger notification if no new items found', async () => {
         (jobsApi.getJobs as any).mockResolvedValue({ total: 0, items: [] });
         
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [{...mockSavedConfigs[0], notify: true}] }));

         await act(async () => {
             result.current.startWatching();
         });

         await waitFor(() => {
             expect(jobsApi.getJobs).toHaveBeenCalled();
         });

         expect(notificationService.notify).not.toHaveBeenCalled();
    });
});
