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

describe('skillsApi - bulkCreateSkills', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should bulk create skills', async () => {
        mocks.post.mockResolvedValueOnce({ data: 3 });
        
        const skills = [
            { name: 'Python', description: 'A programming language', learningPath: [] },
            { name: 'JavaScript', description: 'Web language', learningPath: [] },
            { name: 'Go', description: 'Systems language', learningPath: [] },
        ];
        
        const result = await skillsApi.bulkCreateSkills(skills);
        
        expect(result).toBe(3);
        expect(mocks.post).toHaveBeenCalledWith(
            expect.stringContaining('/skills'),
            expect.arrayContaining([
                expect.objectContaining({ name: 'Python' }),
                expect.objectContaining({ name: 'JavaScript' }),
                expect.objectContaining({ name: 'Go' }),
            ])
        );
    });

    it('should handle disabled field in bulk create', async () => {
        mocks.post.mockResolvedValueOnce({ data: 1 });
        
        const skills = [
            { name: 'Python', description: 'A programming language', learningPath: [], disabled: true },
        ];
        
        await skillsApi.bulkCreateSkills(skills);
        
        expect(mocks.post).toHaveBeenCalledWith(
            expect.any(String),
            expect.arrayContaining([
                expect.objectContaining({ disabled: true }),
            ])
        );
    });
});
