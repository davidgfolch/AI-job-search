import apiClient from '../../common/api/ApiClient';
import type { JobListParams } from './ViewerApi';

export interface FilterConfiguration {
    id: number;
    name: string;
    filters: JobListParams;
    watched: boolean;
    statistics: boolean;
    pinned: boolean;
    ordering: number;
    created: string;
    modified: string | null;
}

export interface FilterConfigurationCreate {
    name: string;
    filters: JobListParams;
    watched?: boolean;
    statistics?: boolean;
    pinned?: boolean;
    ordering?: number;
}

export interface FilterConfigurationUpdate {
    name?: string;
    filters?: JobListParams;
    watched?: boolean;
    statistics?: boolean;
    pinned?: boolean;
    ordering?: number;
}

export const filterConfigsApi = {
    getAll: async (): Promise<FilterConfiguration[]> => {
        const response = await apiClient.get('/filter-configurations');
        return response.data;
    },

    create: async (config: FilterConfigurationCreate): Promise<FilterConfiguration> => {
        const response = await apiClient.post('/filter-configurations', config);
        return response.data;
    },

    update: async (id: number, data: FilterConfigurationUpdate): Promise<FilterConfiguration> => {
        const response = await apiClient.put(`/filter-configurations/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await apiClient.delete(`/filter-configurations/${id}`);
    }
};
