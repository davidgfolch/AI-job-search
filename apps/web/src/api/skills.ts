import axios from 'axios';

export interface Skill {
  name: string;
  description: string;
  learningPath: string[];
  disabled?: boolean;
  ai_enriched?: boolean;
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
      ai_enriched: s.ai_enriched,
    })) as Skill[];
  },

  getSkill: async (name: string): Promise<Skill | null> => {
    try {
      // Since we don't have a single skill endpoint (unless I missed it, listing shows list),
      // Actually backend repo has find_by_name... do we have an endpoint?
      // checking api/skills.py in backend... 
      // It has create, update, delete, bulk create. It does NOT have get_skill(name).
      // I generally need to add it or use list_skills filtering?
      // Wait, list_skills returns all. Polling list_skills is inefficient.
      // I should add get_skill endpoint in backend if it doesn't exist.
      // Or I can rely on list_skills for now if list is small? No, "AI Job Search" sounds like it might have many skills.
      // Let's assume I need to add get_skill endpoint or check if I missed it.
      // Backend api/skills.py lines 1-39 shown in step 58:
      // @router.get("", response_model=List[Skill])
      // @router.post("", ...)
      // @router.post("/{name}", ...)
      // @router.put("/{name}", ...)
      // @router.delete("/{name}")
      // NO GET /{name}!
      // I MUST ADD GET /{name} to backend first!
      // I will implement getSkill here assuming I will add the endpoint.
      const response = await apiClient.get<any>(`/skills/${name}`);
      return {
          ...response.data,
          learningPath: response.data.learning_path || response.data.learningPath || [],
          ai_enriched: response.data.ai_enriched,
      } as Skill;
    } catch (e) {
      return null;
    }
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
      disabled: skill.disabled,
      ai_enriched: skill.ai_enriched
    };
    // The SkillCreate model in backend expects learning_path
    // We should probably map it here.
    const payloadToSend: any = {
      ...payload,
      learning_path: skill.learningPath
    };
    if (skill.ai_enriched !== undefined) payloadToSend.ai_enriched = skill.ai_enriched;

    const response = await apiClient.post<string>(`/skills/${skill.name}`, payloadToSend);
    return response.data;
  },

  updateSkill: async (name: string, skill: Partial<Skill>): Promise<string> => {
    const payload: any = { ...skill };
    if (skill.learningPath) {
      payload.learning_path = skill.learningPath;
      delete payload.learningPath;
    }
    if (skill.ai_enriched !== undefined) {
        payload.ai_enriched = skill.ai_enriched;
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
