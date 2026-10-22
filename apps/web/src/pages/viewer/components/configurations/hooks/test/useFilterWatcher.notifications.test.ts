import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { notificationService } from '../../../../../../common/services/NotificationService';
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
         
         const config1 = { ...mockSavedConfigs[0], watched: true };
         const config2 = { ...mockSavedConfigs[1], watched: true };
         
         const { wrapper } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [config1, config2] }), { wrapper });

         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });

         await waitFor(() => {
             expect(notificationService.notify).toHaveBeenCalledWith(
                 expect.stringContaining('New jobs found'),
                 expect.objectContaining({ 
                     body: expect.stringMatching(/Config 1 \(5\)/) 
                 })
             );
         });
         expect(notificationService.notify).toHaveBeenCalledWith(
             expect.stringContaining('New jobs found'),
             expect.objectContaining({ 
                 body: expect.stringMatching(/Config 2 \(5\)/) 
             })
         );
    });

    it('should notify a loaded configuration when new matches arrive', async () => {
         // The configuration was loaded: its cutoff is now, so the backend reports
         // no new match yet.
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 5, new_items: 0 }, 2: { total: 5, new_items: 0 } });

         const config1 = { ...mockSavedConfigs[0], watched: true };
         const config2 = { ...mockSavedConfigs[1], watched: true };

         const { wrapper, queryClient } = createWrapper();
         const { result } = renderHook(() => useFilterWatcher({ savedConfigs: [config1, config2] }), { wrapper });

         await waitFor(() => {
             expect(jobsApi.getWatcherStats).toHaveBeenCalled();
         });
         expect(notificationService.notify).not.toHaveBeenCalled();

         act(() => {
             result.current.resetWatcher('Config 1');
         });

         // A new match arrives for the loaded configuration.
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 6, new_items: 1 }, 2: { total: 5, new_items: 0 } });
         act(() => {
             queryClient.setQueryData(['jobs'], []);
         });

         await waitFor(() => {
             expect(result.current.results['Config 1'].newItems).toBe(1);
         });
         await waitFor(() => {
             expect(notificationService.notify).toHaveBeenCalledWith(
                 expect.stringContaining('New jobs found'),
                 expect.objectContaining({
                     body: expect.stringMatching(/Config 1 \(1\)/)
                 })
             );
         });
    });

    it('should NOT make API calls for unwatched configs', async () => {
         // With the new behavior, configs with watched=false are filtered out before API calls
         const config1 = { ...mockSavedConfigs[0], watched: false };
         
         const { wrapper } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [config1] }), { wrapper });

         // Wait for the effect to run and ensure no API calls are made
         await waitFor(() => expect(jobsApi.getWatcherStats).not.toHaveBeenCalled());

          // Should NOT make any API calls since the config is not watched
          expect(notificationService.notify).not.toHaveBeenCalled();
    });

    it('should NOT trigger notification if no new items found', async () => {
         (jobsApi.getWatcherStats as any).mockResolvedValue({ 1: { total: 0, new_items: 0 } });
         
         const { wrapper, queryClient } = createWrapper();
         renderHook(() => useFilterWatcher({ savedConfigs: [{...mockSavedConfigs[0], watched: true}] }), { wrapper });

         await waitFor(() => expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(1));
         
         act(() => {
             queryClient.setQueryData(['jobs'], []);
         });

         await waitFor(() => expect(jobsApi.getWatcherStats).toHaveBeenCalledTimes(2));

         expect(notificationService.notify).not.toHaveBeenCalled();
    });
});
