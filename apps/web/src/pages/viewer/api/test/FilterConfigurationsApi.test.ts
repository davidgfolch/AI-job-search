import { describe, it, expect, vi, beforeEach } from 'vitest';
import { filterConfigsApi, type FilterConfiguration, type FilterConfigurationCreate, type FilterConfigurationUpdate } from '../FilterConfigurationsApi';

vi.mock('../../../common/api/ApiClient', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
    },
}));

import apiClient from '../../../common/api/ApiClient';

const mockConfig: FilterConfiguration = {
    id: 1, name: 'Config 1', filters: {}, watched: false, statistics: true, pinned: false, ordering: 0, created: '2024-01-01', modified: null
};

describe('FilterConfigurationsApi', () => {
    beforeEach(() => vi.clearAllMocks());

    describe('getAll', () => {
        it.each([
            [[mockConfig]],
            [[]],
        ])('fetches all filter configurations: %j', async ([data]) => {
            vi.mocked(apiClient.get).mockResolvedValueOnce({ data });
            expect(await filterConfigsApi.getAll()).toEqual(data);
            expect(apiClient.get).toHaveBeenCalledWith('/filter-configurations');
        });

        it('handles API errors', async () => {
            vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Network Error'));
            await expect(filterConfigsApi.getAll()).rejects.toThrow('Network Error');
        });
    });

    describe('create', () => {
        it.each([
            [{ name: 'Config', filters: { search: 'test' }, watched: true, statistics: false } as FilterConfigurationCreate],
            [{ name: 'Min Config', filters: {} } as FilterConfigurationCreate],
        ])('creates config: %j', async (newConfig) => {
            const created = { id: 1, ...newConfig, pinned: false, ordering: 0, created: '2024-01-01', modified: null };
            vi.mocked(apiClient.post).mockResolvedValueOnce({ data: created });
            expect(await filterConfigsApi.create(newConfig)).toEqual(created);
            expect(apiClient.post).toHaveBeenCalledWith('/filter-configurations', newConfig);
        });
    });

    describe('update', () => {
        it.each([
            [1, { name: 'Updated', watched: true } as FilterConfigurationUpdate],
            [2, { pinned: true } as FilterConfigurationUpdate],
        ])('updates config id=%i', async (id, updateData) => {
            const updated = { ...mockConfig, id, ...updateData };
            vi.mocked(apiClient.put).mockResolvedValueOnce({ data: updated });
            expect(await filterConfigsApi.update(id, updateData)).toEqual(updated);
            expect(apiClient.put).toHaveBeenCalledWith(`/filter-configurations/${id}`, updateData);
        });
    });

    describe('delete', () => {
        it('deletes a filter configuration', async () => {
            vi.mocked(apiClient.delete).mockResolvedValueOnce({});
            await filterConfigsApi.delete(1);
            expect(apiClient.delete).toHaveBeenCalledWith('/filter-configurations/1');
        });

        it('handles delete errors', async () => {
            vi.mocked(apiClient.delete).mockRejectedValueOnce(new Error('Delete failed'));
            await expect(filterConfigsApi.delete(1)).rejects.toThrow('Delete failed');
        });
    });
});
