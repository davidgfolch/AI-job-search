import axios from 'axios';

export interface Skill {
  name: string;
  description: string;
  learningPath: string[];
  disabled?: boolean;
}

const API_BASE_URL = 'http://localhost:8000/api';

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
    })) as Skill[];
  },

  createSkill: async (skill: Skill): Promise<string> => {
    // For manual creation/API, we might need to adjust the payload if the backend expects different structure
    // But our models map 1:1 roughly.
    // Note: Backend bulk_create expects List[Skill] for migration
    // Single create expects SkillCreate
    const payload = {
      name: skill.name,
      description: skill.description,
      learning_path: skill.learningPath, // Map camelCase to snake_case? 
      // Wait, backend Pydantic model uses snake_case: `learning_path`
      // But frontend Skill interface uses `learningPath`
      // We need to map it.
      disabled: skill.disabled
    };
    // The SkillCreate model in backend expects learning_path
    // We should probably map it here.
    const response = await apiClient.post<string>(`/skills/${skill.name}`, {
      ...payload,
      learning_path: skill.learningPath
    });
    return response.data;
  },

  updateSkill: async (name: string, skill: Partial<Skill>): Promise<string> => {
    const payload: any = { ...skill };
    if (skill.learningPath) {
      payload.learning_path = skill.learningPath;
      delete payload.learningPath;
    }
    const response = await apiClient.put<string>(`/skills/${name}`, payload);
    return response.data;
  },

  deleteSkill: async (name: string): Promise<void> => {
    await apiClient.delete(`/skills/${name}`);
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
