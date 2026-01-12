import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useLearnList, Skill } from '../useLearnList';
import { skillsApi } from '../../../api/skills';

// Mock the skills API
vi.mock('../../../api/skills', () => ({
    skillsApi: {
        getSkills: vi.fn(),
        createSkill: vi.fn(),
        updateSkill: vi.fn(),
        deleteSkill: vi.fn(),
    }
}));

const mockSkills: Skill[] = [
    { name: 'React', description: 'Frontend lib', learningPath: [], disabled: false },
    { name: 'Node', description: 'Backend runtime', learningPath: ['Basics'], disabled: true },
    { name: 'EmptySkill', description: '', learningPath: [], disabled: false },
];

describe('useLearnList', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch skills on mount', async () => {
        vi.mocked(skillsApi.getSkills).mockResolvedValue(mockSkills);

        const { result } = renderHook(() => useLearnList());

        expect(result.current.isLoading).toBe(true);
        expect(result.current.learnList).toEqual([]);

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.learnList).toEqual(mockSkills);
        expect(result.current.error).toBeNull();
    });

    it('should handle fetch error', async () => {
        vi.mocked(skillsApi.getSkills).mockRejectedValue(new Error('Fetch failed'));

        const { result } = renderHook(() => useLearnList());

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.error).toBe('Failed to load skills from database');
        expect(result.current.learnList).toEqual([]);
    });

    it('toggleSkill should create skill if it does not exist', async () => {
        vi.mocked(skillsApi.getSkills).mockResolvedValue([]);
        vi.mocked(skillsApi.createSkill).mockResolvedValue('success');

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.toggleSkill('Vue');
        });

        expect(skillsApi.createSkill).toHaveBeenCalledWith(expect.objectContaining({
            name: 'Vue',
            disabled: false
        }));
        // Expect fetch to be called again
        expect(skillsApi.getSkills).toHaveBeenCalledTimes(2); 
    });

    it('toggleSkill should re-enable skill if it is disabled', async () => {
        vi.mocked(skillsApi.getSkills).mockResolvedValue(mockSkills);
        vi.mocked(skillsApi.updateSkill).mockResolvedValue('success');

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.toggleSkill('Node'); // Node is disabled in mockSkills
        });

        expect(skillsApi.updateSkill).toHaveBeenCalledWith('Node', { disabled: false });
        expect(skillsApi.getSkills).toHaveBeenCalledTimes(2);
    });

    it('toggleSkill should disable (soft delete) skill if it is enabled and exists', async () => {
        // Checking internal logic of toggle -> removeSkill -> logic
        // removeSkill logic: if content exists, soft delete. 'React' has description.
        vi.mocked(skillsApi.getSkills).mockResolvedValue(mockSkills);
        vi.mocked(skillsApi.updateSkill).mockResolvedValue('success');

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.toggleSkill('React');
        });

        // React has content, so it should be soft deleted (disabled)
        expect(skillsApi.updateSkill).toHaveBeenCalledWith('React', { disabled: true });
        expect(skillsApi.getSkills).toHaveBeenCalledTimes(2);
    });

    it('removeSkill should hard delete if skill has no content', async () => {
        vi.mocked(skillsApi.getSkills).mockResolvedValue(mockSkills);
        vi.mocked(skillsApi.deleteSkill).mockResolvedValue();

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.removeSkill('EmptySkill');
        });

        expect(skillsApi.deleteSkill).toHaveBeenCalledWith('EmptySkill');
        expect(skillsApi.getSkills).toHaveBeenCalledTimes(2);
    });

    it('isInLearnList should return true only for enabled skills', async () => {
        vi.mocked(skillsApi.getSkills).mockResolvedValue(mockSkills);

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.isInLearnList('React')).toBe(true);
        expect(result.current.isInLearnList('Node')).toBe(false); // disabled
        expect(result.current.isInLearnList('Ghost')).toBe(false);
    });
});
