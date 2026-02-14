import { vi, describe, it, expect, afterEach } from 'vitest';
import { skillsApi } from '../SkillsManagerApi';

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}));

vi.mock('axios', () => {
    return {
        default: {
            create: vi.fn(() => ({
                get: mocks.get,
                post: mocks.post,
                put: mocks.put,
                delete: mocks.delete,
            })),
        }
    };
});

describe('skillsApi - getSkills', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch and transform skills', async () => {
        const backendResponse = [
            {
                name: 'Python',
                description: 'A programming language',
                learning_path: ['Learn variables'],
                ai_enriched: true,
                category: 'Programming',
            }
        ];
        mocks.get.mockResolvedValueOnce({ data: backendResponse });
        
        const skills = await skillsApi.getSkills();
        
        expect(skills).toHaveLength(1);
        expect(skills[0].name).toBe('Python');
        expect(skills[0].learningPath).toEqual(['Learn variables']);
        expect(skills[0].ai_enriched).toBe(true);
        expect(skills[0].category).toBe('Programming');
    });

    it('should handle missing learning_path', async () => {
        const backendResponse = [
            { name: 'Python', description: 'A programming language' }
        ];
        mocks.get.mockResolvedValueOnce({ data: backendResponse });
        
        const skills = await skillsApi.getSkills();
        
        expect(skills[0].learningPath).toEqual([]);
    });

    it('should handle learningPath in camelCase', async () => {
        const backendResponse = [
            { name: 'Python', description: 'A programming language', learningPath: ['Test'] }
        ];
        mocks.get.mockResolvedValueOnce({ data: backendResponse });
        
        const skills = await skillsApi.getSkills();
        
        expect(skills[0].learningPath).toEqual(['Test']);
    });
});
