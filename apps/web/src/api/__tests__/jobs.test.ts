import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jobsApi } from '../jobs';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => {
    const mockAxios = {
        get: vi.fn(),
        patch: vi.fn(),
        create: vi.fn(() => mockAxios),
    };
    return { default: mockAxios };
});

describe('jobsApi', () => {
    const mockAxios = axios as any;

    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('getJobs', () => {
        it('fetches jobs with default parameters', async () => {
            const mockResponse = {
                data: {
                    items: [],
                    total: 0,
                    page: 1,
                    size: 20,
                },
            };
            mockAxios.get.mockResolvedValue(mockResponse);

            const result = await jobsApi.getJobs();

            expect(mockAxios.get).toHaveBeenCalledWith('/jobs', { params: {} });
            expect(result).toEqual(mockResponse.data);
        });

        it('fetches jobs with custom parameters', async () => {
            const params = {
                page: 2,
                search: 'React',
                flagged: true,
            };
            const mockResponse = { data: { items: [], total: 0 } };
            mockAxios.get.mockResolvedValue(mockResponse);

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

    describe('updateJob', () => {
        it('updates a job with partial data', async () => {
            const updateData = { flagged: true, comments: 'Test' };
            const mockUpdatedJob = { id: 1, ...updateData };
            mockAxios.patch.mockResolvedValue({ data: mockUpdatedJob });

            const result = await jobsApi.updateJob(1, updateData);

            expect(mockAxios.patch).toHaveBeenCalledWith('/jobs/1', updateData);
            expect(result).toEqual(mockUpdatedJob);
        });
    });
});
