import apiClient from '../../common/api/ApiClient';

export interface SynonymGroup {
  group_id: number;
  names: string[];
}

export const companySynonymsApi = {
  listGroups: async (): Promise<SynonymGroup[]> => {
    const response = await apiClient.get<SynonymGroup[]>('/company-synonyms');
    return response.data;
  },

  getSynonyms: async (company: string): Promise<string[]> => {
    const response = await apiClient.get<string[]>('/company-synonyms/synonyms', {
      params: { company },
    });
    return response.data;
  },

  createGroup: async (names: string[]): Promise<{ group_id: number }> => {
    const response = await apiClient.post<{ group_id: number }>('/company-synonyms/groups', { names });
    return response.data;
  },

  addToGroup: async (groupId: number, name: string): Promise<void> => {
    await apiClient.post(`/company-synonyms/groups/${groupId}`, { name });
  },

  removeName: async (name: string): Promise<void> => {
    await apiClient.delete(`/company-synonyms/names/${encodeURIComponent(name)}`);
  },
};
