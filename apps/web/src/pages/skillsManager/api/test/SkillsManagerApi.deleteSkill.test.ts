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

describe('skillsApi - deleteSkill', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should delete a skill', async () => {
        mocks.delete.mockResolvedValueOnce({});
        
        await skillsApi.deleteSkill('Python');
        
        expect(mocks.delete).toHaveBeenCalledWith(expect.stringContaining('/skills/Python'));
    });
});
