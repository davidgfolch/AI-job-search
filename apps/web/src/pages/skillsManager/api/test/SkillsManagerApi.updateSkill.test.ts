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

describe('skillsApi - updateSkill', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should update a skill', async () => {
        mocks.put.mockResolvedValueOnce({ data: 'Updated' });
        
        const result = await skillsApi.updateSkill('Python', { description: 'New description' });
        
        expect(result).toBe('Updated');
        expect(mocks.put).toHaveBeenCalled();
    });

    it('should transform learningPath to learning_path', async () => {
        mocks.put.mockResolvedValueOnce({ data: 'Updated' });
        
        await skillsApi.updateSkill('Python', { learningPath: ['New path'] });
        
        expect(mocks.put).toHaveBeenCalledWith(
            expect.any(String),
            expect.objectContaining({
                learning_path: ['New path'],
            })
        );
    });
});
