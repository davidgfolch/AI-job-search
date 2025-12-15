import { describe, it, expect, vi, beforeEach } from 'vitest';
import { jobsApi } from '../jobs';
const mocks = vi.hoisted(() => ({
    axiosCreateConfig: { value: null as any },
    axiosInstance: {
        get: vi.fn(),
        patch: vi.fn(),
    }
}));

// Mock axios
vi.mock('axios', () => {
    return {
        default: {
            create: vi.fn((config) => {
                mocks.axiosCreateConfig.value = config;
                return mocks.axiosInstance;
            }),
        },
    };
});

describe('jobsApi', () => {
    const mockAxios = mocks.axiosInstance;

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

    describe('getAppliedJobsByCompany', () => {
        it('fetches applied jobs for a company', async () => {
            const mockAppliedJobs = [{ id: 1, created: '2023-01-01' }];
            mockAxios.get.mockResolvedValue({ data: mockAppliedJobs });

            const result = await jobsApi.getAppliedJobsByCompany('Test Company');

            expect(mockAxios.get).toHaveBeenCalledWith('/jobs/applied-by-company', {
                params: { company: 'Test Company' }
            });
            expect(result).toEqual(mockAppliedJobs);
        });

        it('fetches applied jobs for a company and client', async () => {
            const mockAppliedJobs = [{ id: 1, created: '2023-01-01' }];
            mockAxios.get.mockResolvedValue({ data: mockAppliedJobs });

            const result = await jobsApi.getAppliedJobsByCompany('Test Company', 'Client A');

            expect(mockAxios.get).toHaveBeenCalledWith('/jobs/applied-by-company', {
                params: { company: 'Test Company', client: 'Client A' }
            });
            expect(result).toEqual(mockAppliedJobs);
        });
    });

    describe('error handling', () => {
        it('throws an error with the correct message when request fails', async () => {
            const errorMessage = 'Network Error';
            mockAxios.get.mockRejectedValue(new Error(errorMessage));

            await expect(jobsApi.getJobs()).rejects.toThrow(`Error loading jobs: ${errorMessage}`);
        });

        it('throws an error with string message when non-Error object is thrown', async () => {
            const errorMessage = 'Unknown error';
            mockAxios.get.mockRejectedValue(errorMessage);

            await expect(jobsApi.getJobs()).rejects.toThrow(`Error loading jobs: ${errorMessage}`);
        });
    });

    describe('paramsSerializer', () => {
        it('correctly serializes complex parameters', () => {
            const serializer = mocks.axiosCreateConfig.value.paramsSerializer;
            const params = {
                page: 1,
                ids: [1, 2, 3],
                nullVal: null,
                undefinedVal: undefined,
                search: 'test'
            };

            const result = serializer(params);
            const searchParams = new URLSearchParams(result);

            expect(searchParams.get('page')).toBe('1');
            expect(searchParams.getAll('ids')).toEqual(['1', '2', '3']);
            expect(searchParams.get('search')).toBe('test');
            expect(searchParams.has('nullVal')).toBe(false);
            expect(searchParams.has('undefinedVal')).toBe(false);
        });
    });
});

// To properly test paramsSerializer, we need to spy on the config passed to axios.create
// or refactor the code to make paramsSerializer exportable. 
// Let's modify the mock to capture the config.
