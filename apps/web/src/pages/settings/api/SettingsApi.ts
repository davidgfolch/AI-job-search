import apiClient from '../../common/api/ApiClient';

export interface SettingsEnvUpdateDto {
    key: string;
    value: string;
}

/** Free-form scraper state persisted by the backend; the payload is not schema constrained. */
export type ScrapperState = Record<string, unknown>;

export interface ScrapperStateUpdateDto {
    state: ScrapperState;
}

export const settingsApi = {
    getEnvSettings: async (): Promise<Record<string, string>> => {
        const response = await apiClient.get<Record<string, string>>('/settings/env');
        return response.data;
    },

    updateEnvSetting: async (key: string, value: string): Promise<Record<string, string>> => {
        const response = await apiClient.post<Record<string, string>>('/settings/env', { key, value });
        return response.data;
    },

    updateEnvSettingsBulk: async (updates: Record<string, string>): Promise<Record<string, string>> => {
        const response = await apiClient.post<Record<string, string>>('/settings/env-bulk', { updates });
        return response.data;
    },

    getScrapperState: async (): Promise<ScrapperState> => {
        const response = await apiClient.get<ScrapperState>('/settings/scrapper-state');
        return response.data;
    },

    updateScrapperState: async (state: ScrapperState): Promise<ScrapperState> => {
        const response = await apiClient.post<ScrapperState>('/settings/scrapper-state', { state });
        return response.data;
    }
};
