import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday } from '../StatisticsApi';
import type { HistoryStat, SourceDateStat, SourceHourStat, SourceWeekdayStat } from '../StatisticsApi';

const mockApiClient = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('../../../common/api/ApiClient', () => ({
  default: mockApiClient,
}));

describe('StatisticsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getHistoryStats', () => {
    it('fetches history statistics successfully', async () => {
      const mockData: HistoryStat[] = [{
        dateCreated: '2024-01-01',
        applied: 5,
        discarded: 3,
        interview: 2,
        discarded_cumulative: 10,
        interview_cumulative: 4,
      }];
      mockApiClient.get.mockResolvedValue({ data: mockData });
      const result = await getHistoryStats();
      expect(mockApiClient.get).toHaveBeenCalledWith('/statistics/history', { params: expect.any(URLSearchParams) });
      expect(result).toEqual(mockData);
    });

    it('propagates errors', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API error'));
      await expect(getHistoryStats()).rejects.toThrow('API error');
    });
  });

  describe('getSourcesByDate', () => {
    it('fetches sources by date successfully', async () => {
      const mockData: SourceDateStat[] = [{
        dateCreated: '2024-01-01',
        total: 10,
        source: 'LinkedIn',
      }];
      mockApiClient.get.mockResolvedValue({ data: mockData });
      const result = await getSourcesByDate();
      expect(mockApiClient.get).toHaveBeenCalledWith('/statistics/sources-date', { params: expect.any(URLSearchParams) });
      expect(result).toEqual(mockData);
    });
  });

  describe('getSourcesByHour', () => {
    it('fetches sources by hour successfully', async () => {
      const mockData: SourceHourStat[] = [{
        hour: 9,
        total: 15,
        source: 'Indeed',
      }];
      mockApiClient.get.mockResolvedValue({ data: mockData });
      const result = await getSourcesByHour();
      expect(mockApiClient.get).toHaveBeenCalledWith('/statistics/sources-hour', { params: expect.any(URLSearchParams) });
      expect(result).toEqual(mockData);
    });
  });

  describe('getSourcesByWeekday', () => {
    it('fetches sources by weekday successfully', async () => {
      const mockData: SourceWeekdayStat[] = [{
        weekday: 1,
        total: 20,
        source: 'Monster',
      }];
      mockApiClient.get.mockResolvedValue({ data: mockData });
      const result = await getSourcesByWeekday();
      expect(mockApiClient.get).toHaveBeenCalledWith('/statistics/sources-weekday', { params: expect.any(URLSearchParams) });
      expect(result).toEqual(mockData);
    });
  });
});
