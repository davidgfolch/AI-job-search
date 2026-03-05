import apiClient from './ApiClient';

export interface DdlSchemaResponse {
    tables: Record<string, string[]>;
    keywords: string[];
}

export const fetchDdlSchema = async (): Promise<DdlSchemaResponse> => {
    const response = await apiClient.get('/ddl/schema');
    return response.data;
};

export const getModalityValues = async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>('/ddl/schema/enum-values/jobs/modality');
    return response.data;
};
