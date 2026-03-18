import { vi } from 'vitest';

export const mockGetHistoryStats = vi.fn().mockResolvedValue([{ total: 10 }]);
export const mockGetSourcesByDate = vi.fn().mockResolvedValue([{ source: 'A', dateCreated: '2024-01-01', total: 5 }]);
export const mockGetSourcesByHour = vi.fn().mockResolvedValue([{ source: 'B', hour: 12, total: 3 }]);
export const mockGetSourcesByWeekday = vi.fn().mockResolvedValue([{ source: 'C', weekday: 1, total: 7 }]);
export const mockGetFilterConfigStats = vi.fn().mockResolvedValue([{ name: 'Filter 1', count: 12 }]);

// Mocking chartUtils as well if needed, but since we rely on actual process logic for coverage, we won't mock chartUtils.

vi.mock('../api/StatisticsApi', () => ({
    getHistoryStats: mockGetHistoryStats,
    getSourcesByDate: mockGetSourcesByDate,
    getSourcesByHour: mockGetSourcesByHour,
    getSourcesByWeekday: mockGetSourcesByWeekday,
    getFilterConfigStats: mockGetFilterConfigStats,
}));
