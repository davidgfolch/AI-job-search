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

describe('skillsApi - getSkill', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch a single skill', async () => {
        const backendResponse = {
            name: 'Python',
            description: 'A programming language',
            learning_path: ['Learn variables'],
            ai_enriched: true,
            category: 'Programming',
        };
        mocks.get.mockResolvedValueOnce({ data: backendResponse });
        
        const skill = await skillsApi.getSkill('Python');
        
        expect(skill).not.toBeNull();
        expect(skill?.name).toBe('Python');
        expect(skill?.learningPath).toEqual(['Learn variables']);
    });

    it('should return null on error', async () => {
        mocks.get.mockRejectedValueOnce(new Error('Not found'));
        
        const skill = await skillsApi.getSkill('NonExistent');
        
        expect(skill).toBeNull();
    });
});
