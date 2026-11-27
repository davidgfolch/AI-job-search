import apiClient from '../../common/api/ApiClient';

export type LearningPathSource = 'llm' | 'duckduckgo' | 'manual' | 'unknown';

export interface LearningPathLink {
  url: string;
  source: LearningPathSource;
}

export interface Skill {
  name: string;
  description: string;
  learningPath: LearningPathLink[];
  disabled?: boolean;
  ai_enriched?: boolean;
  category?: string;
}

/** The backend names the field in snake case and may still return legacy plain-string links. */
type LearningPathResponse = Array<LearningPathLink | string>;

interface SkillResponse {
  name: string;
  description: string;
  learning_path?: LearningPathResponse;
  learningPath?: LearningPathResponse;
  disabled?: boolean;
  ai_enriched?: boolean;
  category?: string;
}

const normalizeLink = (link: LearningPathLink | string): LearningPathLink =>
  typeof link === 'string' ? { url: link, source: 'unknown' } : { url: link.url, source: link.source || 'unknown' };

const normalizeLearningPath = (links?: LearningPathResponse): LearningPathLink[] => (links || []).map(normalizeLink);

export const skillsApi = {
  getSkills: async (): Promise<Skill[]> => {
    const response = await apiClient.get<SkillResponse[]>('/skills');
    return response.data.map((s) => ({
      ...s,
      learningPath: normalizeLearningPath(s.learning_path || s.learningPath),
      ai_enriched: s.ai_enriched,
      category: s.category,
    }));
  },

  getSkill: async (name: string): Promise<Skill | null> => {
    try {
      const response = await apiClient.get<SkillResponse>(`/skills/${encodeURIComponent(name)}`);
      return {
          ...response.data,
          learningPath: normalizeLearningPath(response.data.learning_path || response.data.learningPath),
          ai_enriched: response.data.ai_enriched,
          category: response.data.category,
      };
    } catch {
      return null;
    }
  },

  createSkill: async (skill: Skill): Promise<string> => {
    const payloadToSend: Record<string, unknown> = {
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
    const payload: Record<string, unknown> = { ...skill };
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
