import { vi } from 'vitest';

export const mockSavedConfigs = [
    { name: 'Config 1', filters: { search: 'python' } },
    { name: 'Config 2', filters: { location: 'remote' } }
];

export const setupMocks = () => {
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
};

export const cleanupMocks = () => {
    vi.clearAllMocks();
    vi.useRealTimers();
};
