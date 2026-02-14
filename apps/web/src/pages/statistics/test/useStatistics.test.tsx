import { describe, it, expect, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStatistics } from '../useStatistics';
import * as StatisticsApi from '../api/StatisticsApi';

vi.mock('../api/StatisticsApi');

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useStatistics', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
    });

    it('returns default time range', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.timeRange).toBe('All'));
        expect(result.current.timeRange).toBe('All');
    });

    it('updates time range', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.timeRange).toBe('All'));
        
        await act(async () => {
            result.current.setTimeRange('Last week');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last week'));
    });

    it('updates time range to Last year', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.timeRange).toBe('All'));
        
        await act(async () => {
            result.current.setTimeRange('Last year');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last year'));
    });

    it('updates time range to Last 6 months', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.timeRange).toBe('All'));
        
        await act(async () => {
            result.current.setTimeRange('Last 6 months');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last 6 months'));
    });

    it('updates time range to Last month', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.timeRange).toBe('All'));
        
        await act(async () => {
            result.current.setTimeRange('Last month');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last month'));
    });

    it('updates time range to Last day', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.timeRange).toBe('All'));
        
        await act(async () => {
            result.current.setTimeRange('Last day');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last day'));
    });

    it('returns empty data arrays initially', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        await waitFor(() => expect(result.current.historyData).toBeDefined());
        expect(result.current.historyData).toEqual([]);
        expect(result.current.sourcesDateWide).toEqual([]);
        expect(result.current.sourcesHourWide).toEqual([]);
        expect(result.current.sourcesWeekdayWide).toEqual([]);
    });

    it('processes API data correctly', async () => {
        const mockSourcesDateData = [
            { dateCreated: '2024-01-01', source: 'LinkedIn', total: 10 },
            { dateCreated: '2024-01-01', source: 'Indeed', total: 5 },
        ];
        const mockSourcesHourData = [
            { hour: 9, source: 'LinkedIn', total: 8 },
        ];
        const mockSourcesWeekdayData = [
            { weekday: 1, source: 'LinkedIn', total: 3 },
        ];
        
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue(mockSourcesDateData);
        vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue(mockSourcesHourData);
        vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue(mockSourcesWeekdayData);

        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        
        await waitFor(() => expect(result.current.sourcesDateWide.length).toBeGreaterThan(0));
        expect(result.current.sourcesDateKeys).toContain('LinkedIn');
        expect(result.current.sourcesDateKeys).toContain('Indeed');
    });

    it('returns filter config data', async () => {
        const mockFilterConfigData = [{ name: 'Config1', count: 10 }];
        vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue(mockFilterConfigData as any);

        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        
        await waitFor(() => expect(result.current.filterConfigData).toEqual(mockFilterConfigData));
    });

    it('computes allSources from multiple keys', async () => {
        const mockSourcesDateData = [{ dateCreated: '2024-01-01', source: 'LinkedIn', total: 10 }];
        const mockSourcesHourData = [{ hour: 9, source: 'Indeed', total: 8 }];
        const mockSourcesWeekdayData = [{ weekday: 1, source: 'Glassdoor', total: 3 }];
        
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue(mockSourcesDateData);
        vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue(mockSourcesHourData);
        vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue(mockSourcesWeekdayData);

        const { result } = renderHook(() => useStatistics(), { wrapper: createWrapper() });
        
        await waitFor(() => expect(result.current.allSources.length).toBe(3));
        expect(result.current.allSources).toContain('LinkedIn');
        expect(result.current.allSources).toContain('Indeed');
        expect(result.current.allSources).toContain('Glassdoor');
    });
});
