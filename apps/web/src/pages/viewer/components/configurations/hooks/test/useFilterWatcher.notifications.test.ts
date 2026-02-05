import { renderHook, waitFor } from '@testing-library/react';
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
        renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }), { wrapper: createWrapper() });
        
        await waitFor(() => {
            expect(notificationService.requestPermission).toHaveBeenCalled();
        });
    });

    it('should trigger aggregated notification for enabled configs', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 5 }, 2: { total: 5, new_items: 5 } });
         
         const config1 = { ...mockSavedConfigs[0], notify: true };
         const config2 = { ...mockSavedConfigs[1], notify: true };
         
         renderHook(() => useFilterWatcher({ savedConfigs: [config1, config2] }), { wrapper: createWrapper() });

         // Automatically triggered on mount
         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1);
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
         
         renderHook(() => useFilterWatcher({ savedConfigs: [config1] }), { wrapper: createWrapper() });

         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });

         expect(notificationService.notify).not.toHaveBeenCalled();
    });

    it('should NOT trigger notification if no new items found', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 0, new_items: 0 } });
         
         renderHook(() => useFilterWatcher({ savedConfigs: [{...mockSavedConfigs[0], notify: true}] }), { wrapper: createWrapper() });

         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });

         expect(notificationService.notify).not.toHaveBeenCalled();
    });
});
