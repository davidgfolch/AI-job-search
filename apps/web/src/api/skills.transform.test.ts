import { vi, describe, it, expect, afterEach } from 'vitest';

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

import { skillsApi } from './skills';

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

        // Act
        const skills = await skillsApi.getSkills();

        // Assert
        expect(skills).toHaveLength(1);
        expect(skills[0].name).toBe('Python');
        // This expectation should fail currently as mapping is missing
        expect(skills[0].learningPath).toEqual(['Learn variables', 'Learn loops']);
    });
});
