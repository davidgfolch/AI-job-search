import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStatistics } from '../useStatistics';
import * as StatisticsApi from '../api/StatisticsApi';

vi.mock('../api/StatisticsApi');

const testQueryClient = new QueryClient({
    defaultOptions: {
        queries: { retry: false },
    },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
);

describe('useStatistics', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        testQueryClient.clear();
        vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getKeywordStats).mockResolvedValue([]);
    });

    it('returns default time range', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.timeRange).toBe('Last 3 months'));
        expect(result.current.timeRange).toBe('Last 3 months');
    });

    it('updates time range', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.timeRange).toBe('Last 3 months'));
        
        await act(async () => {
            result.current.setTimeRange('Last week');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last week'));
    });

    it('updates time range to Last year', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.timeRange).toBe('Last 3 months'));
        
        await act(async () => {
            result.current.setTimeRange('Last year');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last year'));
    });

    it('updates time range to Last 6 months', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.timeRange).toBe('Last 3 months'));
        
        await act(async () => {
            result.current.setTimeRange('Last 6 months');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last 6 months'));
    });

    it('updates time range to Last month', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.timeRange).toBe('Last 3 months'));
        
        await act(async () => {
            result.current.setTimeRange('Last month');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last month'));
    });

    it('updates time range to Last day', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.timeRange).toBe('Last 3 months'));
        
        await act(async () => {
            result.current.setTimeRange('Last day');
        });
        
        await waitFor(() => expect(result.current.timeRange).toBe('Last day'));
    });

    it('returns empty data arrays initially', async () => {
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.historyData).toBeDefined());
        expect(result.current.historyData).toEqual([]);
        expect(result.current.sourcesDateWide).toEqual([]);
        expect(result.current.sourcesHourWide).toEqual([]);
        expect(result.current.sourcesWeekdayWide).toEqual([]);
    });

    it('defaults to the Linkedin site filter and filters source charts', async () => {
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([
            { dateCreated: '2024-01-01', source: 'Linkedin', total: 10 },
            { dateCreated: '2024-01-01', source: 'Indeed', total: 5 },
            { dateCreated: '2024-01-01', source: 'Glassdoor', total: 3 },
        ]);
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.sourcesDateWide.length).toBeGreaterThan(0));
        expect(result.current.site).toBe('Linkedin');
        expect(result.current.sourcesDateKeys).toEqual(['Linkedin']);
        await act(async () => { result.current.setSite('(All)'); });
        await waitFor(() => expect(result.current.sourcesDateKeys).toEqual(['Linkedin', 'Indeed']));
    });

    it('returns filter config data', async () => {
        const mockFilterConfigData = [{ name: 'Config1', count: 10 }];
        vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue(mockFilterConfigData as any);

        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        
        await waitFor(() => expect(result.current.filterConfigData).toEqual(mockFilterConfigData));
    });

    it('filters keyword stats by site and allows scraper sites in (All)', async () => {
        const keywordData = [
            { date: '2026-11-19', site: 'Linkedin', keyword: 'python', reported_total: 40, processed: 20, new: 18, duplicates: 2, duplicate_ids: '91,92' },
            { date: '2026-11-19', site: 'Indeed', keyword: 'python', reported_total: 5, processed: 5, new: 1, duplicates: 4, duplicate_ids: '7' },
            { date: '2026-11-19', site: 'Glassdoor', keyword: 'python', reported_total: 99, processed: 99, new: 50, duplicates: 49, duplicate_ids: '77' },
        ];
        vi.mocked(StatisticsApi.getKeywordStats).mockResolvedValue(keywordData);
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await waitFor(() => expect(result.current.keywordStats).toHaveLength(1));
        expect(result.current.keywordStats).toEqual([keywordData[0]]);
        await act(async () => { result.current.setSite('(All)'); });
        await waitFor(() => expect(result.current.keywordStats).toHaveLength(2));
        expect(result.current.keywordStats).toEqual([keywordData[0], keywordData[1]]);
    });

    it('computes allSources from allowed sites across charts', async () => {
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([{ dateCreated: '2024-01-01', source: 'Linkedin', total: 10 }]);
        vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([{ hour: 9, source: 'Indeed', total: 8 }]);
        vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([{ weekday: 1, source: 'Infojobs', total: 3 }]);
        const { result } = renderHook(() => useStatistics(), { wrapper: wrapper });
        await act(async () => { result.current.setSite('(All)'); });
        await waitFor(() => expect(result.current.allSources.length).toBe(3));
        expect(result.current.allSources).toEqual(expect.arrayContaining(['Linkedin', 'Indeed', 'Infojobs']));
    });
});
