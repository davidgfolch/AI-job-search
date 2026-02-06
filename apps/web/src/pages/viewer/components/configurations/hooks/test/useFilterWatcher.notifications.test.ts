import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { notificationService } from '../../../../../../common/services/NotificationService';
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

describe('useFilterWatcher - Notifications', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mock implementation to prevent undefined errors
        (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 0, new_items: 0 }, 2: { total: 0, new_items: 0 } });
    });

    afterEach(() => {
        cleanupMocks();
    });

    it('should request notification permission on mount when isWatching is true', async () => {
        const { wrapper } = createWrapper();
        renderHook(() => useFilterWatcher({ savedConfigs: [mockSavedConfigs[0]] }), { wrapper });
        
        await waitFor(() => {
            expect(notificationService.requestPermission).toHaveBeenCalled();
        });
    });

    it('should trigger aggregated notification for enabled configs', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 5 }, 2: { total: 5, new_items: 5 } });
         
         const config1 = { ...mockSavedConfigs[0], notify: true };
         const config2 = { ...mockSavedConfigs[1], notify: true };
         
         const { wrapper, queryClient } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [config1, config2] }), { wrapper });

         // First check: newItems should be 0 (due to justReset protection)
         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
         });
         expect(notificationService.notify).not.toHaveBeenCalled();

         // Second check: server returns 0 (catching up)
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 0 }, 2: { total: 5, new_items: 0 } });
         act(() => {
             queryClient.setQueryData(['jobs'], []);
         });
         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2);
         });
         expect(notificationService.notify).not.toHaveBeenCalled();

         // Third check: server returns 5 (new items arrive after catch-up)
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 10, new_items: 5 }, 2: { total: 10, new_items: 5 } });
         act(() => {
             queryClient.setQueryData(['jobs'], []);
         });
         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(3);
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
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 5 } });
         
         const config1 = { ...mockSavedConfigs[0], notify: false };
         
         const { wrapper, queryClient } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [config1] }), { wrapper });

         // We need two checks here as well if we want to test disabled notifications
         await waitFor(() => expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1));
         
         act(() => {
             queryClient.setQueryData(['jobs'], []);
         });

         await waitFor(() => expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2));

         expect(notificationService.notify).not.toHaveBeenCalled();
    });

    it('should NOT trigger notification if no new items found', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 0, new_items: 0 } });
         
         const { wrapper, queryClient } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [{...mockSavedConfigs[0], notify: true}] }), { wrapper });

         await waitFor(() => expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1));
         
         act(() => {
             queryClient.setQueryData(['jobs'], []);
         });

         await waitFor(() => expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2));

         expect(notificationService.notify).not.toHaveBeenCalled();
    });
});
