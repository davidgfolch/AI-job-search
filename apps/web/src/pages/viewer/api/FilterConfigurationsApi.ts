import axios from 'axios';
import type { JobListParams } from './ViewerApi';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export interface FilterConfiguration {
    id: number;
    name: string;
    filters: JobListParams;
    notify: boolean;
    created: string;
    modified: string | null;
}

export interface FilterConfigurationCreate {
    name: string;
    filters: JobListParams;
    notify?: boolean;
}

export interface FilterConfigurationUpdate {
    name?: string;
    filters?: JobListParams;
    notify?: boolean;
}

export const filterConfigsApi = {
    getAll: async (): Promise<FilterConfiguration[]> => {
        const response = await axios.get(`${API_BASE_URL}/filter-configurations`);
        return response.data;
    },

    create: async (config: FilterConfigurationCreate): Promise<FilterConfiguration> => {
        const response = await axios.post(`${API_BASE_URL}/filter-configurations`, config);
        return response.data;
    },

    update: async (id: number, data: FilterConfigurationUpdate): Promise<FilterConfiguration> => {
        const response = await axios.put(`${API_BASE_URL}/filter-configurations/${id}`, data);
        return response.data;
    },

    delete: async (id: number): Promise<void> => {
        await axios.delete(`${API_BASE_URL}/filter-configurations/${id}`);
    }
};
