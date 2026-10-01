import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { useCompanySynonyms } from '../useCompanySynonyms';

const mockClient = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn(), delete: vi.fn() }));
vi.mock('axios', () => ({ default: { create: vi.fn(() => mockClient) } }));

const createWrapper = () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0, staleTime: 0, retryDelay: 0 }, mutations: { retry: false } } });
    return ({ children }: { children: ReactNode }) => <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};

describe('useCompanySynonyms', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const renderHookSettled = async () => {
        const utils = renderHook(() => useCompanySynonyms(), { wrapper: createWrapper() });
        await waitFor(() => expect(utils.result.current.isLoading).toBe(false), { timeout: 1000, interval: 10 });
        return utils;
    };

    it('lists groups from GET /company-synonyms', async () => {
        const groups = [{ group_id: 1, names: ['Acme'] }];
        mockClient.get.mockResolvedValue({ data: groups });
        const { result } = await renderHookSettled();
        expect(mockClient.get).toHaveBeenCalledWith('/company-synonyms');
        expect(result.current.groups).toEqual(groups);
        expect(result.current.error).toBeNull();
    });

    it('defaults to an empty list and surfaces the error when the query fails', async () => {
        mockClient.get.mockRejectedValue(new Error('backend down'));
        const { result } = await renderHookSettled();
        expect(result.current.groups).toEqual([]);
        expect(result.current.error).toBeTruthy();
    });

    it('creates a group with POST /company-synonyms/groups', async () => {
        mockClient.get.mockResolvedValue({ data: [] });
        mockClient.post.mockResolvedValue({ data: { group_id: 3 } });
        const { result } = await renderHookSettled();
        await act(async () => { await result.current.createGroup(['Acme', 'Acme Inc']); });
        expect(mockClient.post).toHaveBeenCalledWith('/company-synonyms/groups', { names: ['Acme', 'Acme Inc'] });
    });

    it('adds a name to a group with POST /company-synonyms/groups/:id', async () => {
        mockClient.get.mockResolvedValue({ data: [] });
        mockClient.post.mockResolvedValue({ data: undefined });
        const { result } = await renderHookSettled();
        await act(async () => { await result.current.addToGroup({ groupId: 4, name: 'Acme Ltd' }); });
        expect(mockClient.post).toHaveBeenCalledWith('/company-synonyms/groups/4', { name: 'Acme Ltd' });
    });

    it('removes a name with DELETE on the url-encoded path', async () => {
        mockClient.get.mockResolvedValue({ data: [] });
        mockClient.delete.mockResolvedValue({ data: undefined });
        const { result } = await renderHookSettled();
        await act(async () => { await result.current.removeName('Acme & Co'); });
        expect(mockClient.delete).toHaveBeenCalledWith('/company-synonyms/names/Acme%20%26%20Co');
    });

    it('rejects the mutation promise when the api fails, so the caller can await it', async () => {
        mockClient.get.mockResolvedValue({ data: [] });
        mockClient.post.mockRejectedValue(new Error('nope'));
        const { result } = await renderHookSettled();
        await expect(act(async () => { await result.current.createGroup(['Acme', 'Acme Inc']); })).rejects.toThrow('nope');
    });
});