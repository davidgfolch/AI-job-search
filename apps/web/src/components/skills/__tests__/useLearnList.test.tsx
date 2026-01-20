import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useLearnList, type Skill } from '../useLearnList';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

const mockClient = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }));
vi.mock('axios', () => ({ default: { create: vi.fn(() => mockClient) } }));

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
                gcTime: 0,
                staleTime: 0,
                retryDelay: 0
            } 
        } 
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

const setupHook = async (mockData: Skill[] | Error = mockSkills) => {
    vi.clearAllMocks();
    if (mockData instanceof Error) mockClient.get.mockRejectedValue(mockData);
    else mockClient.get.mockResolvedValue({ data: mockData });

    const utils = renderHook(() => useLearnList(), { wrapper: createWrapper() });
    
    // Waiting for the initial fetch to settle is unavoidable for most tests
    // but ensuring we don't wait longer than needed
    await waitFor(() => expect(utils.result.current.isLoading).toBe(false), { timeout: 1000, interval: 10 });
    return utils;
};

describe('useLearnList', () => {
    it('should fetch skills on mount', async () => {
        const { result } = await setupHook();
        expect(result.current.learnList).toEqual(mockSkills);
        expect(result.current.error).toBeNull();
        expect(mockClient.get).toHaveBeenCalledWith('/skills');
    });

    it('should handle fetch error', async () => {
        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        const { result } = await setupHook(new Error('Fetch failed'));
        expect(result.current.error).toBe('Failed to load skills from database');
        expect(result.current.learnList).toEqual([]);
        consoleSpy.mockRestore();
    });

    it.each([
        { name: 'Vue', initial: [], action: 'create', method: 'post', expectedCall: { name: 'Vue', disabled: false } },
        { name: 'Node', initial: mockSkills, action: 'enable', method: 'put', expectedCall: { disabled: false } }, // Node is disabled
        { name: 'React', initial: mockSkills, action: 'disable', method: 'put', expectedCall: { disabled: true } }  // React is enabled
    ])('toggleSkill should $action skill', async ({ name, initial, method, expectedCall }) => {
        const { result } = await setupHook(initial);
        mockClient[method as 'post' | 'put'].mockResolvedValue({ data: 'success' });
        mockClient.get.mockResolvedValueOnce({ data: mockSkills }); // Re-fetch mock

        await act(async () => await result.current.toggleSkill(name));

        expect(mockClient[method as 'post' | 'put']).toHaveBeenCalledWith(`/skills/${name}`, expect.objectContaining(expectedCall));
        await waitFor(() => expect(mockClient.get).toHaveBeenCalledTimes(2));
    });

    it('removeSkill should hard delete if skill has no content', async () => {
        const { result } = await setupHook();
        mockClient.delete.mockResolvedValue({ data: 'success' });
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });

        await act(async () => await result.current.removeSkill('EmptySkill'));

        expect(mockClient.delete).toHaveBeenCalledWith('/skills/EmptySkill');
        await waitFor(() => expect(mockClient.get).toHaveBeenCalledTimes(2));
    });

    it('isInLearnList should check visibility', async () => {
        const { result } = await setupHook();
        expect(result.current.isInLearnList('React')).toBe(true);
        expect(result.current.isInLearnList('Node')).toBe(false);
        expect(result.current.isInLearnList('Ghost')).toBe(false);
    });

    it('reorders skills locally', async () => {
        const { result } = await setupHook();
        const newOrder = [mockSkills[1], mockSkills[0], mockSkills[2]];
        await act(async () => await result.current.reorderSkills(newOrder));
        await waitFor(() => expect(result.current.learnList).toEqual(newOrder));
    });

    it('updates skill details via API', async () => {
        const { result } = await setupHook();
        mockClient.put.mockResolvedValue({ data: 'success' });
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });

        await act(async () => await result.current.updateSkill('React', { description: 'Updated' }));

        expect(mockClient.put).toHaveBeenCalledWith('/skills/React', expect.objectContaining({ description: 'Updated' }));
        await waitFor(() => expect(mockClient.get).toHaveBeenCalledTimes(2));
    });

    it('saveSkill creates new skill if not exists', async () => {
        const { result } = await setupHook();
        mockClient.post.mockResolvedValue({ data: 'success' });
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });

        await act(async () => await result.current.saveSkill({ 
            name: 'NewSkill', 
            description: 'New Description', 
            learningPath: [] 
        }));

        expect(mockClient.post).toHaveBeenCalledWith('/skills/NewSkill', expect.objectContaining({ 
            name: 'NewSkill',
            description: 'New Description'
        }));
        await waitFor(() => expect(mockClient.get).toHaveBeenCalledTimes(2));
    });

    it('saveSkill updates existing skill', async () => {
        const { result } = await setupHook();
        mockClient.put.mockResolvedValue({ data: 'success' });
        mockClient.get.mockResolvedValueOnce({ data: mockSkills });

        await act(async () => await result.current.saveSkill({ 
            name: 'React', // Existing in mockSkills
            description: 'Updated Description', 
            learningPath: [] 
        }));

        expect(mockClient.put).toHaveBeenCalledWith('/skills/React', expect.objectContaining({ 
            description: 'Updated Description'
        }));
        await waitFor(() => expect(mockClient.get).toHaveBeenCalledTimes(2));
    });
});
