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

describe('skillsApi - createSkill', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should create a skill', async () => {
        mocks.post.mockResolvedValueOnce({ data: 'Created' });
        
        const skill = {
            name: 'Python',
            description: 'A programming language',
            learningPath: ['Learn variables'],
        };
        
        const result = await skillsApi.createSkill(skill);
        
        expect(result).toBe('Created');
        expect(mocks.post).toHaveBeenCalledWith(
            expect.stringContaining('/skills/Python'),
            expect.objectContaining({
                name: 'Python',
                description: 'A programming language',
                learning_path: ['Learn variables'],
            })
        );
    });

    it('should handle optional fields', async () => {
        mocks.post.mockResolvedValueOnce({ data: 'Created' });
        
        const skill = {
            name: 'Python',
            description: 'A programming language',
            learningPath: [],
            disabled: true,
            ai_enriched: true,
            category: 'Programming',
        };
        
        await skillsApi.createSkill(skill);
        
        expect(mocks.post).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                disabled: true,
                ai_enriched: true,
                category: 'Programming',
            })
        );
    });
});
