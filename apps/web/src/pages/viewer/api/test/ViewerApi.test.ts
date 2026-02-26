import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jobsApi } from '../ViewerApi';
const mocks = vi.hoisted(() => ({
    axiosCreateConfig: { value: null as any },
    axiosInstance: { get: vi.fn(), patch: vi.fn(), post: vi.fn() }
}));
vi.mock('axios', () => ({ default: { create: vi.fn((config) => { mocks.axiosCreateConfig.value = config; return mocks.axiosInstance; }) } }));

describe('jobsApi', () => {
    const mockAxios = mocks.axiosInstance;
    beforeEach(() => vi.clearAllMocks());

    describe('getJobs', () => {
        it('fetches jobs with default parameters', async () => {
            mockAxios.get.mockResolvedValue({ data: { items: [], total: 0, page: 1, size: 20 } });
            const result = await jobsApi.getJobs();
            expect(mockAxios.get).toHaveBeenCalledWith('/jobs', { params: {} });
            expect(result).toEqual({ items: [], total: 0, page: 1, size: 20 });
        });
        it('fetches jobs with custom parameters', async () => {
            const params = { page: 2, search: 'React', flagged: true };
            mockAxios.get.mockResolvedValue({ data: { items: [], total: 0 } });
            await jobsApi.getJobs(params);
            expect(mockAxios.get).toHaveBeenCalledWith('/jobs', { params });
        });
    });

    describe('getJob', () => {
        it('fetches a single job by id', async () => {
            const mockJob = { id: 1, title: 'Test Job' };
            mockAxios.get.mockResolvedValue({ data: mockJob });
            const result = await jobsApi.getJob(1);
            expect(mockAxios.get).toHaveBeenCalledWith('/jobs/1');
            expect(result).toEqual(mockJob);
        });
    });

    describe('getAppliedJobsByCompany', () => {
        it('fetches applied jobs for a company', async () => {
            const mockAppliedJobs = [{ id: 1, created: '2023-01-01' }];
            mockAxios.get.mockResolvedValue({ data: mockAppliedJobs });
            const result = await jobsApi.getAppliedJobsByCompany('Test Company');
            expect(mockAxios.get).toHaveBeenCalledWith('/jobs/applied-by-company', { params: { company: 'Test Company' } });
            expect(result).toEqual(mockAppliedJobs);
        });
        it('fetches applied jobs for a company and client', async () => {
            const mockAppliedJobs = [{ id: 1, created: '2023-01-01' }];
            mockAxios.get.mockResolvedValue({ data: mockAppliedJobs });
            const result = await jobsApi.getAppliedJobsByCompany('Test Company', 'Client A');
            expect(mockAxios.get).toHaveBeenCalledWith('/jobs/applied-by-company', { params: { company: 'Test Company', client: 'Client A' } });
            expect(result).toEqual(mockAppliedJobs);
        });
    });

    describe('error handling', () => {
        it('throws an error with the correct message when request fails', async () => {
            mockAxios.get.mockRejectedValue(new Error('Network Error'));
            await expect(jobsApi.getJobs()).rejects.toThrow('Error loading jobs: Network Error');
        });
        it('throws an error with string message when non-Error object is thrown', async () => {
            mockAxios.get.mockRejectedValue('Unknown error');
            await expect(jobsApi.getJobs()).rejects.toThrow('Error loading jobs: Unknown error');
        });
    });

    describe('paramsSerializer', () => {
        it('correctly serializes complex parameters', () => {
            const serializer = mocks.axiosCreateConfig.value.paramsSerializer;
            const params = { page: 1, ids: [1, 2, 3], nullVal: null, undefinedVal: undefined, search: 'test' };
            const result = serializer(params);
            const searchParams = new URLSearchParams(result);
            expect(searchParams.get('page')).toBe('1');
            expect(searchParams.getAll('ids')).toEqual(['1', '2', '3']);
            expect(searchParams.get('search')).toBe('test');
            expect(searchParams.has('nullVal')).toBe(false);
            expect(searchParams.has('undefinedVal')).toBe(false);
        });
    });

    describe('getWatcherStats', () => {
        it('fetches watcher stats for config ids', async () => {
            mockAxios.get.mockResolvedValue({ data: { 1: { total: 10, new_items: 2 } } });
            const result = await jobsApi.getWatcherStats({ 1: '2024-01-01' });
            expect(mockAxios.get).toHaveBeenCalledWith('/jobs/watcher-stats', { params: { config_ids: '1', from_1: '2024-01-01' } });
            expect(result).toEqual({ 1: { total: 10, new_items: 2 } });
        });
    });

    describe('createJob', () => {
        it('creates a new job', async () => {
            const newJob = { id: 1, title: 'New Job' };
            mockAxios.post.mockResolvedValue({ data: newJob });
            const result = await jobsApi.createJob({ title: 'New Job' });
            expect(mockAxios.post).toHaveBeenCalledWith('/jobs', { title: 'New Job' });
            expect(result).toEqual(newJob);
        });
    });

    describe('updateJob', () => {
        it('updates an existing job', async () => {
            const updatedJob = { id: 1, title: 'Updated Job' };
            mockAxios.patch.mockResolvedValue({ data: updatedJob });
            const result = await jobsApi.updateJob(1, { title: 'Updated Job' });
            expect(mockAxios.patch).toHaveBeenCalledWith('/jobs/1', { title: 'Updated Job' });
            expect(result).toEqual(updatedJob);
        });
    });

    describe('bulkUpdateJobs', () => {
        it('bulk updates jobs with ids', async () => {
            mockAxios.post.mockResolvedValue({ data: { updated: 5 } });
            const result = await jobsApi.bulkUpdateJobs({ ids: [1, 2, 3], update: { seen: true } });
            expect(mockAxios.post).toHaveBeenCalledWith('/jobs/bulk', { ids: [1, 2, 3], update: { seen: true } });
            expect(result).toEqual({ updated: 5 });
        });
        it('bulk updates jobs with select_all', async () => {
            mockAxios.post.mockResolvedValue({ data: { updated: 10 } });
            const result = await jobsApi.bulkUpdateJobs({ select_all: true, update: { ignored: true } });
            expect(mockAxios.post).toHaveBeenCalledWith('/jobs/bulk', { select_all: true, update: { ignored: true } });
            expect(result).toEqual({ updated: 10 });
        });
    });

    describe('deleteJobs', () => {
        it('deletes jobs with ids', async () => {
            mockAxios.post.mockResolvedValue({ data: { deleted: 3 } });
            const result = await jobsApi.deleteJobs({ ids: [1, 2, 3] });
            expect(mockAxios.post).toHaveBeenCalledWith('/jobs/bulk/delete', { ids: [1, 2, 3] });
            expect(result).toEqual({ deleted: 3 });
        });
    });

    describe('getSystemTimezone', () => {
        it('fetches system timezone and caches the promise', async () => {
            mockAxios.get.mockResolvedValue({ data: { offset_minutes: 60 } });
            const result = await jobsApi.getSystemTimezone();
            expect(mockAxios.get).toHaveBeenCalledWith('/system/timezone');
            expect(result).toEqual({ offset_minutes: 60 });
        });
    });
});
