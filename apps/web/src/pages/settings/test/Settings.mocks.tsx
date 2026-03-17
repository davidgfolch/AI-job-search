import { vi } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { settingsApi } from '../api/SettingsApi';
import { groupSettingsByKey, getSubgroupTitle } from '../utils/SettingsUtils';
import { mockGroupedSettings, mockEnvSettings, mockScrapperState } from './Settings.fixtures';

export const createTestQueryClient = () => new QueryClient({
    defaultOptions: {
        queries: { retry: false },
    },
});

export const setupSettingsMocks = () => {
    vi.clearAllMocks();
    vi.mocked(groupSettingsByKey).mockReturnValue(mockGroupedSettings);
    vi.mocked(getSubgroupTitle).mockImplementation((key) => {
        if (key.startsWith('PREFIX_')) return 'PREFIX_SUBGROUP';
        return key;
    });
    vi.mocked(settingsApi.getEnvSettings).mockResolvedValue(mockEnvSettings);
    vi.mocked(settingsApi.getScrapperState).mockResolvedValue(mockScrapperState);
    vi.mocked(settingsApi.updateEnvSettingsBulk).mockImplementation(async (settings) => settings);
    vi.mocked(settingsApi.updateScrapperState).mockImplementation(async (state) => state);
};

export const renderWithClient = (ui: React.ReactElement) => {
    const testQueryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={testQueryClient}>
            {ui}
        </QueryClientProvider>
    );
};
