import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    getHistoryStats, getSourcesByDate, getSourcesByHour,
    getSourcesByWeekday, getFilterConfigStats
} from '../StatisticsApi';

const mockApiClient = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock('../../../common/api/ApiClient', () => ({ default: mockApiClient }));

const START = '2024-01-01';
const END = '2024-12-31';

describe('StatisticsApi', () => {
    beforeEach(() => vi.clearAllMocks());

    const call_cases = [
        { fn: getHistoryStats,      endpoint: '/statistics/history',        name: 'getHistoryStats' },
        { fn: getSourcesByDate,     endpoint: '/statistics/sources-date',    name: 'getSourcesByDate' },
        { fn: getSourcesByHour,     endpoint: '/statistics/sources-hour',    name: 'getSourcesByHour' },
        { fn: getSourcesByWeekday,  endpoint: '/statistics/sources-weekday', name: 'getSourcesByWeekday' },
        { fn: getFilterConfigStats, endpoint: '/statistics/filter-configs',  name: 'getFilterConfigStats' },
    ] as const;

    it.each(call_cases)('$name calls correct endpoint without date params', async ({ fn, endpoint }) => {
        mockApiClient.get.mockResolvedValue({ data: [] });
        await fn();
        expect(mockApiClient.get).toHaveBeenCalledWith(endpoint, { params: {} });
    });

    it.each(call_cases)('$name passes date params as plain object', async ({ fn, endpoint }) => {
        mockApiClient.get.mockResolvedValue({ data: [] });
        await fn(START, END);
        expect(mockApiClient.get).toHaveBeenCalledWith(endpoint, {
            params: { start_date: START, end_date: END },
        });
    });

    it.each(call_cases)('$name propagates errors', async ({ fn }) => {
        mockApiClient.get.mockRejectedValue(new Error('API error'));
        await expect(fn()).rejects.toThrow('API error');
    });
});
