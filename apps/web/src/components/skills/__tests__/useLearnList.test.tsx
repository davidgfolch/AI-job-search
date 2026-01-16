import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useLearnList, Skill } from '../useLearnList';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

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

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useLearnList', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should fetch skills on mount', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });

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

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.error).toBe('Failed to load skills from database');
        expect(result.current.learnList).toEqual([]);
        consoleSpy.mockRestore();
    });

    it('toggleSkill should create skill if it does not exist', async () => {
        mockClient.get.mockResolvedValueOnce({ data: [] }); // Initial fetch
        mockClient.post.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        // Setup get for re-fetch (invalidation)
        mockClient.get.mockResolvedValueOnce({ data: [{ name: 'Vue', disabled: false } as Skill] });

        await act(async () => {
            await result.current.toggleSkill('Vue');
        });

        expect(mockClient.post).toHaveBeenCalledWith('/skills/Vue', expect.objectContaining({
            name: 'Vue',
            disabled: false
        }));
        
        await waitFor(() => {
             expect(mockClient.get).toHaveBeenCalledTimes(2);
        });
    });

    it('toggleSkill should re-enable skill if it is disabled', async () => {
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });
        mockClient.put.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        // Refetch setup
        mockClient.get.mockResolvedValueOnce({ data: mockSkills }); 

        await act(async () => {
            await result.current.toggleSkill('Node'); // Node is disabled in mockSkills
        });

        expect(mockClient.put).toHaveBeenCalledWith('/skills/Node', expect.objectContaining({ disabled: false }));
        
        await waitFor(() => {
             expect(mockClient.get).toHaveBeenCalledTimes(2);
        });
    });

    it('toggleSkill should disable (soft delete) skill if it is enabled and exists', async () => {
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });
        mockClient.put.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

         // Refetch setup
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });

        await act(async () => {
            await result.current.toggleSkill('React');
        });

        expect(mockClient.put).toHaveBeenCalledWith('/skills/React', expect.objectContaining({ disabled: true }));
        
        await waitFor(() => {
             expect(mockClient.get).toHaveBeenCalledTimes(2);
        });
    });

    it('removeSkill should hard delete if skill has no content', async () => {
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });
        mockClient.delete.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

         // Refetch setup
        mockClient.get.mockResolvedValueOnce({ data: mockSkills }); 

        await act(async () => {
            await result.current.removeSkill('EmptySkill');
        });

        expect(mockClient.delete).toHaveBeenCalledWith('/skills/EmptySkill');
        
        await waitFor(() => {
             expect(mockClient.get).toHaveBeenCalledTimes(2);
        });
    });

    it('isInLearnList should return true only for enabled skills', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.isInLearnList('React')).toBe(true);
        expect(result.current.isInLearnList('Node')).toBe(false); // disabled
        expect(result.current.isInLearnList('Ghost')).toBe(false);
    });

    it('reorders skills (client side only)', async () => {
        mockClient.get.mockResolvedValue({ data: mockSkills });
        
        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        const newOrder = [mockSkills[1], mockSkills[0], mockSkills[2]];
        
        await act(async () => {
            await result.current.reorderSkills(newOrder);
        });

        await waitFor(() => {
            expect(result.current.learnList).toEqual(newOrder);
        });
    });

    it('updates skill details via API', async () => {
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });
        mockClient.put.mockResolvedValue({ data: 'success' });

        const { result } = renderHook(() => useLearnList(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        // Refetch setup
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });

        await act(async () => {
            await result.current.updateSkill('React', { description: 'Updated Desc' });
        });

        expect(mockClient.put).toHaveBeenCalledWith('/skills/React', expect.objectContaining({ description: 'Updated Desc' }));
        await waitFor(() => {
             expect(mockClient.get).toHaveBeenCalledTimes(2);
        });
    });
});
