import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday } from '../StatisticsApi';
import type { HistoryStat, SourceDateStat, SourceHourStat, SourceWeekdayStat } from '../StatisticsApi';

const mockAxios = vi.hoisted(() => ({
  get: vi.fn(),
}));

vi.mock('axios', () => ({
  default: mockAxios,
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
      mockAxios.get.mockResolvedValue({ data: mockData });
      const result = await getHistoryStats();
      expect(mockAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/statistics/history', { params: expect.any(URLSearchParams) });
      expect(result).toEqual(mockData);
    });

    it('propagates errors', async () => {
      mockAxios.get.mockRejectedValue(new Error('API error'));
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
      mockAxios.get.mockResolvedValue({ data: mockData });
      const result = await getSourcesByDate();
      expect(mockAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/statistics/sources-date', { params: expect.any(URLSearchParams) });
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
      mockAxios.get.mockResolvedValue({ data: mockData });
      const result = await getSourcesByHour();
      expect(mockAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/statistics/sources-hour', { params: expect.any(URLSearchParams) });
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
      mockAxios.get.mockResolvedValue({ data: mockData });
      const result = await getSourcesByWeekday();
      expect(mockAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/statistics/sources-weekday', { params: expect.any(URLSearchParams) });
      expect(result).toEqual(mockData);
    });
  });
});
