import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { filterConfigsApi, type FilterConfiguration, type FilterConfigurationCreate, type FilterConfigurationUpdate } from '../FilterConfigurationsApi';

vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('FilterConfigurationsApi', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getAll', () => {
        it('fetches all filter configurations', async () => {
            const mockData: FilterConfiguration[] = [
                { id: 1, name: 'Config 1', filters: {}, watched: false, statistics: true, pinned: false, ordering: 0, created: '2024-01-01', modified: null },
                { id: 2, name: 'Config 2', filters: {}, watched: true, statistics: false, pinned: true, ordering: 1, created: '2024-01-02', modified: '2024-01-03' },
            ];
            mockedAxios.get.mockResolvedValueOnce({ data: mockData });

            const result = await filterConfigsApi.getAll();

            expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringContaining('/filter-configurations'));
            expect(result).toEqual(mockData);
        });

        it('handles API errors', async () => {
            mockedAxios.get.mockRejectedValueOnce(new Error('Network Error'));

            await expect(filterConfigsApi.getAll()).rejects.toThrow('Network Error');
        });
    });

    describe('create', () => {
        it('creates a new filter configuration', async () => {
            const newConfig: FilterConfigurationCreate = {
                name: 'New Config',
                filters: { search: 'test' },
                watched: true,
                statistics: false,
            };
            const createdConfig: FilterConfiguration = { id: 1, ...newConfig, pinned: false, ordering: 0, created: '2024-01-01', modified: null };
            mockedAxios.post.mockResolvedValueOnce({ data: createdConfig });

            const result = await filterConfigsApi.create(newConfig);

            expect(mockedAxios.post).toHaveBeenCalledWith(expect.stringContaining('/filter-configurations'), newConfig);
            expect(result).toEqual(createdConfig);
        });

        it('creates config with minimal data', async () => {
            const newConfig: FilterConfigurationCreate = { name: 'Min Config', filters: {} };
            const createdConfig: FilterConfiguration = { id: 1, ...newConfig, watched: false, statistics: true, pinned: false, ordering: 0, created: '2024-01-01', modified: null };
            mockedAxios.post.mockResolvedValueOnce({ data: createdConfig });

            const result = await filterConfigsApi.create(newConfig);

            expect(result).toEqual(createdConfig);
        });
    });

    describe('update', () => {
        it('updates an existing filter configuration', async () => {
            const updateData: FilterConfigurationUpdate = { name: 'Updated Name', watched: true };
            const updatedConfig: FilterConfiguration = { id: 1, name: 'Updated Name', filters: {}, watched: true, statistics: true, pinned: false, ordering: 0, created: '2024-01-01', modified: '2024-01-02' };
            mockedAxios.put.mockResolvedValueOnce({ data: updatedConfig });

            const result = await filterConfigsApi.update(1, updateData);

            expect(mockedAxios.put).toHaveBeenCalledWith(expect.stringContaining('/filter-configurations/1'), updateData);
            expect(result).toEqual(updatedConfig);
        });

        it('updates config with partial data', async () => {
            const updateData: FilterConfigurationUpdate = { pinned: true };
            const updatedConfig: FilterConfiguration = { id: 1, name: 'Config', filters: {}, watched: false, statistics: true, pinned: true, ordering: 0, created: '2024-01-01', modified: '2024-01-02' };
            mockedAxios.put.mockResolvedValueOnce({ data: updatedConfig });

            const result = await filterConfigsApi.update(1, updateData);

            expect(result).toEqual(updatedConfig);
        });
    });

    describe('delete', () => {
        it('deletes a filter configuration', async () => {
            mockedAxios.delete.mockResolvedValueOnce({});

            await filterConfigsApi.delete(1);

            expect(mockedAxios.delete).toHaveBeenCalledWith(expect.stringContaining('/filter-configurations/1'));
        });

        it('handles delete errors', async () => {
            mockedAxios.delete.mockRejectedValueOnce(new Error('Delete failed'));

            await expect(filterConfigsApi.delete(1)).rejects.toThrow('Delete failed');
        });
    });
});
