import { vi } from 'vitest';
import { settingsApi } from '../api/SettingsApi';
import { groupSettingsByKey, getSubgroupTitle } from '../utils/SettingsUtils';
import { mockGroupedSettings, mockEnvSettings, mockScrapperState } from './Settings.fixtures';



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
