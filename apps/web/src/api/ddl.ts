import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface DdlSchemaResponse {
    tables: Record<string, string[]>;
    keywords: string[];
}

export const fetchDdlSchema = async (): Promise<DdlSchemaResponse> => {
    const response = await axios.get(`${API_URL}/ddl/schema`);
    return response.data;
};
