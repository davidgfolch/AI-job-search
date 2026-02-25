import apiClient from '../../common/api/ApiClient';

export interface SettingsEnvUpdateDto {
    key: string;
    value: string;
}

export interface ScrapperStateUpdateDto {
    state: Record<string, any>;
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

    getScrapperState: async (): Promise<Record<string, any>> => {
        const response = await apiClient.get<Record<string, any>>('/settings/scrapper-state');
        return response.data;
    },

    updateScrapperState: async (state: Record<string, any>): Promise<Record<string, any>> => {
        const response = await apiClient.post<Record<string, any>>('/settings/scrapper-state', { state });
        return response.data;
    }
};
