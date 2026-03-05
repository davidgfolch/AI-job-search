import axios from 'axios';
import apiClient from './ApiClient';

const API_URL = 'http://localhost:8000/api';

export interface DdlSchemaResponse {
    tables: Record<string, string[]>;
    keywords: string[];
}

export const fetchDdlSchema = async (): Promise<DdlSchemaResponse> => {
    const response = await axios.get(`${API_URL}/ddl/schema`);
    return response.data;
};

export const getModalityValues = async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>('/ddl/schema/enum-values/jobs/modality');
    return response.data;
};
