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

describe('skillsApi', () => {
    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should map learning_path (snake_case) to learningPath (camelCase)', async () => {
        // Arrange
        const backendResponse = [
            {
                name: 'Python',
                description: 'A programming language',
                learning_path: ['Learn variables', 'Learn loops'], // Backend sends this
                disabled: false
            }
        ];
        mocks.get.mockResolvedValueOnce({ data: backendResponse });
        const skills = await skillsApi.getSkills();
        expect(skills).toHaveLength(1);
        expect(skills[0].name).toBe('Python');
        expect(skills[0].learningPath).toEqual(['Learn variables', 'Learn loops']);
    });
});
