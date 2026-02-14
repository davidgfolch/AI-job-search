import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Statistics from '../Statistics';
import * as StatisticsApi from '../api/StatisticsApi';

vi.mock('../api/StatisticsApi');
vi.mock('recharts', () => ({
    LineChart: () => null,
    Line: () => null,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => children,
    BarChart: () => null,
    Bar: () => null,
}));

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

describe('Statistics - Extended', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
        vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
    });

    it('renders with all default values', () => {
        render(<Statistics />, { wrapper: createWrapper() });
        expect(screen.getByText('AI Job Search - Statistics')).toBeInTheDocument();
    });

    it('renders date range selector with all options', () => {
        render(<Statistics />, { wrapper: createWrapper() });
        const select = screen.getByRole('combobox');
        
        expect(screen.getByText('Last year')).toBeInTheDocument();
        expect(screen.getByText('Last 6 months')).toBeInTheDocument();
        expect(screen.getByText('Last month')).toBeInTheDocument();
        expect(screen.getByText('Last week')).toBeInTheDocument();
        expect(screen.getByText('Last day')).toBeInTheDocument();
    });

    it('renders three chart sections', () => {
        render(<Statistics />, { wrapper: createWrapper() });
        
        expect(screen.getByText('Job Postings by Source & Day of Week')).toBeInTheDocument();
        expect(screen.getByText('Job Postings by Source & Created Date')).toBeInTheDocument();
        expect(screen.getByText('Job Postings by Source & Day Time')).toBeInTheDocument();
    });

    it('renders filter config chart section', () => {
        render(<Statistics />, { wrapper: createWrapper() });
        expect(screen.getByText('Filter Configurations & Job Counts')).toBeInTheDocument();
    });

    it('renders history chart section', () => {
        render(<Statistics />, { wrapper: createWrapper() });
        expect(screen.getByText('Applied vs Discarded Jobs (History)')).toBeInTheDocument();
    });

    it('renders all layout buttons', () => {
        render(<Statistics />, { wrapper: createWrapper() });
        
        expect(screen.getByTitle('Single Column')).toBeInTheDocument();
        expect(screen.getByTitle('Two Columns')).toBeInTheDocument();
        expect(screen.getByTitle('Three Columns')).toBeInTheDocument();
    });
});
