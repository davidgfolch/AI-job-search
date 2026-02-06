import { vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

export const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
        React.createElement(QueryClientProvider, { client: queryClient }, children)
    );
    return { wrapper, queryClient };
};

export const mockSavedConfigs = [
    { id: 1, name: 'Config 1', filters: { search: 'python' } },
    { id: 2, name: 'Config 2', filters: { location: 'remote' } }
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
