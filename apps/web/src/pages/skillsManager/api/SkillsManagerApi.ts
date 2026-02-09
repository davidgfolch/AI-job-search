import axios from 'axios';

export interface Skill {
  name: string;
  description: string;
  learningPath: string[];
  disabled?: boolean;
  ai_enriched?: boolean;
  category?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const skillsApi = {
  getSkills: async (): Promise<Skill[]> => {
    const response = await apiClient.get<any[]>('/skills');
    return response.data.map((s: any) => ({
      ...s,
      learningPath: s.learning_path || s.learningPath || [],
      ai_enriched: s.ai_enriched,
      category: s.category,
    })) as Skill[];
  },

  getSkill: async (name: string): Promise<Skill | null> => {
    try {
      const response = await apiClient.get<any>(`/skills/${encodeURIComponent(name)}`);
      return {
          ...response.data,
          learningPath: response.data.learning_path || response.data.learningPath || [],
          ai_enriched: response.data.ai_enriched,
          category: response.data.category,
      } as Skill;
    } catch (e) {
      return null;
    }
  },

  createSkill: async (skill: Skill): Promise<string> => {
    const payloadToSend: any = {
      name: skill.name,
      description: skill.description,
      learning_path: skill.learningPath,
      disabled: skill.disabled,
      ai_enriched: skill.ai_enriched,
      category: skill.category
    };

    const response = await apiClient.post<string>(`/skills/${encodeURIComponent(skill.name)}`, payloadToSend);
    return response.data;
  },

  updateSkill: async (name: string, skill: Partial<Skill>): Promise<string> => {
    const payload: any = { ...skill };
    if (skill.learningPath) {
      payload.learning_path = skill.learningPath;
      delete payload.learningPath;
    }
    const response = await apiClient.put<string>(`/skills/${encodeURIComponent(name)}`, payload);
    return response.data;
  },

  deleteSkill: async (name: string): Promise<void> => {
    await apiClient.delete(`/skills/${encodeURIComponent(name)}`);
  },
  
  // For migration
  bulkCreateSkills: async (skills: Skill[]): Promise<number> => {
      const payload = skills.map(s => ({
          name: s.name,
          description: s.description,
          learning_path: s.learningPath,
          disabled: s.disabled
      }));
      const response = await apiClient.post<number>('/skills', payload);
      return response.data;
  }
};
