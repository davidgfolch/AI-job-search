import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFilterWatcher } from '../useFilterWatcher';
import { jobsApi } from '../../../../api/ViewerApi';
import { notificationService } from '../../../../../../common/services/NotificationService';
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

describe('useFilterWatcher - Notifications', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mock implementation to prevent undefined errors
        (jobsApi.countJobs as any).mockResolvedValue(0);
    });

    afterEach(() => {
        cleanupMocks();
    });

    it('should request notification permission on mount when isWatching is true', async () => {
        renderHook(() => useFilterWatcher({ savedConfigs: mockSavedConfigs }));
        
        await waitFor(() => {
            expect(notificationService.requestPermission).toHaveBeenCalled();
        });
    });

    it('should trigger aggregated notification for enabled configs', async () => {
         (jobsApi.countJobs as any).mockResolvedValue(5);
         
         const config1 = { ...mockSavedConfigs[0], notify: true };
         const config2 = { ...mockSavedConfigs[1], notify: true };
         
         renderHook(() => useFilterWatcher({ savedConfigs: [config1, config2] }));

         // Automatically triggered on mount
         await waitFor(() => {
             expect(jobsApi.countJobs).toHaveBeenCalledTimes(4);
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
         (jobsApi.countJobs as any).mockResolvedValue(5);
         
         const config1 = { ...mockSavedConfigs[0], notify: false };
         
         renderHook(() => useFilterWatcher({ savedConfigs: [config1] }));

         await waitFor(() => {
             expect(jobsApi.countJobs).toHaveBeenCalled();
         });

         expect(notificationService.notify).not.toHaveBeenCalled();
    });

    it('should NOT trigger notification if no new items found', async () => {
         (jobsApi.countJobs as any).mockResolvedValue(0);
         
         renderHook(() => useFilterWatcher({ savedConfigs: [{...mockSavedConfigs[0], notify: true}] }));

         await waitFor(() => {
             expect(jobsApi.countJobs).toHaveBeenCalled();
         });

         expect(notificationService.notify).not.toHaveBeenCalled();
    });
});
