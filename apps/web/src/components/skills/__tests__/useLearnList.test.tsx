import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useLearnList, Skill } from '../useLearnList';
import axios from 'axios';

// Define the mock client methods using vi.hoisted so they are available in vi.mock
const mockClient = vi.hoisted(() => ({
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
}));

// Mock axios to return our mock client
vi.mock('axios', () => ({
    default: {
        create: vi.fn(() => mockClient),
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
        // skillsApi.getSkills maps response.data. So we must provide { data: ... }
        mockClient.get.mockResolvedValue({ data: mockSkills });

        const { result } = renderHook(() => useLearnList());

        expect(result.current.isLoading).toBe(true);
        expect(result.current.learnList).toEqual([]);

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.learnList).toEqual(mockSkills);
        expect(result.current.error).toBeNull();
        expect(mockClient.get).toHaveBeenCalledWith('/skills');
    });

    it('should handle fetch error', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        mockClient.get.mockRejectedValue(new Error('Fetch failed'));

        const { result } = renderHook(() => useLearnList());

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.error).toBe('Failed to load skills from database');
        expect(result.current.learnList).toEqual([]);
        consoleSpy.mockRestore();
    });

    it('toggleSkill should create skill if it does not exist', async () => {
        mockClient.get.mockResolvedValue({ data: [] });
        mockClient.post.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        // Setup get for re-fetch
        mockClient.get.mockResolvedValue({ data: [{ name: 'Vue', disabled: false } as Skill] });

        await act(async () => {
            await result.current.toggleSkill('Vue');
        });

        // skillsApi.createSkill POSTs to /skills/Vue with payload
        expect(mockClient.post).toHaveBeenCalledWith('/skills/Vue', expect.objectContaining({
            name: 'Vue',
            disabled: false
        }));
        // Expect fetch to be called again
        expect(mockClient.get).toHaveBeenCalledTimes(2); 
    });

    it('toggleSkill should re-enable skill if it is disabled', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });
        mockClient.put.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.toggleSkill('Node'); // Node is disabled in mockSkills
        });

        // skillsApi.updateSkill PUTs to /skills/Node
        // Payload has disabled: false
        expect(mockClient.put).toHaveBeenCalledWith('/skills/Node', expect.objectContaining({ disabled: false }));
        expect(mockClient.get).toHaveBeenCalledTimes(2);
    });

    it('toggleSkill should disable (soft delete) skill if it is enabled and exists', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });
        mockClient.put.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.toggleSkill('React');
        });

        // React has content, so it should be soft deleted (disabled)
        expect(mockClient.put).toHaveBeenCalledWith('/skills/React', expect.objectContaining({ disabled: true }));
        expect(mockClient.get).toHaveBeenCalledTimes(2);
    });

    it('removeSkill should hard delete if skill has no content', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });
        mockClient.delete.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        await act(async () => {
            await result.current.removeSkill('EmptySkill');
        });

        expect(mockClient.delete).toHaveBeenCalledWith('/skills/EmptySkill');
        expect(mockClient.get).toHaveBeenCalledTimes(2);
    });

    it('isInLearnList should return true only for enabled skills', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });

        const { result } = renderHook(() => useLearnList());
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.isInLearnList('React')).toBe(true);
        expect(result.current.isInLearnList('Node')).toBe(false); // disabled
        expect(result.current.isInLearnList('Ghost')).toBe(false);
    });
});
