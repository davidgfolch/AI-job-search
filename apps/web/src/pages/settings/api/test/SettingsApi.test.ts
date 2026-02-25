import { describe, it, expect, vi, beforeEach } from 'vitest';
import { settingsApi } from '../SettingsApi';
import apiClient from '../../../common/api/ApiClient';

vi.mock('../../../common/api/ApiClient', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
    }
}));

describe('SettingsApi', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('getEnvSettings should return env settings', async () => {
        const mockData = { key1: 'val1', key2: 'val2' };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockData });

        const result = await settingsApi.getEnvSettings();

        expect(apiClient.get).toHaveBeenCalledWith('/settings/env');
        expect(result).toEqual(mockData);
    });

    it('updateEnvSetting should post and return updated settings', async () => {
        const mockData = { key1: 'val1', key2: 'val2', key3: 'val3' };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockData });

        const result = await settingsApi.updateEnvSetting('key3', 'val3');

        expect(apiClient.post).toHaveBeenCalledWith('/settings/env', { key: 'key3', value: 'val3' });
        expect(result).toEqual(mockData);
    });

    it('updateEnvSettingsBulk should post and return bulk updated settings', async () => {
        const updates = { key1: 'val1', key2: 'val2' };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: updates });

        const result = await settingsApi.updateEnvSettingsBulk(updates);

        expect(apiClient.post).toHaveBeenCalledWith('/settings/env-bulk', { updates });
        expect(result).toEqual(updates);
    });

    it('getScrapperState should return scrapper state', async () => {
        const mockData = { lastRun: '2023-01-01', status: 'idle' };
        vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockData });

        const result = await settingsApi.getScrapperState();

        expect(apiClient.get).toHaveBeenCalledWith('/settings/scrapper-state');
        expect(result).toEqual(mockData);
    });

    it('updateScrapperState should post and return updated state', async () => {
        const state = { lastRun: '2023-01-01', status: 'running' };
        vi.mocked(apiClient.post).mockResolvedValueOnce({ data: state });

        const result = await settingsApi.updateScrapperState(state);

        expect(apiClient.post).toHaveBeenCalledWith('/settings/scrapper-state', { state });
        expect(result).toEqual(state);
    });
});
