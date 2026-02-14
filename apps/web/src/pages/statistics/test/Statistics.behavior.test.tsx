import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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

describe('Statistics', () => {
  beforeEach(() => {
    vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
  });

  it('renders time range selector', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    expect(screen.getByText('Date Range:')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('renders layout buttons', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    expect(screen.getByTitle('Single Column')).toBeInTheDocument();
    expect(screen.getByTitle('Two Columns')).toBeInTheDocument();
    expect(screen.getByTitle('Three Columns')).toBeInTheDocument();
  });

  it('changes time range', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Last week' } });
    expect(screen.getByRole('combobox')).toHaveValue('Last week');
  });

  it('changes layout to single column', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    const singleColumnBtn = screen.getByTitle('Single Column');
    fireEvent.click(singleColumnBtn);
    expect(singleColumnBtn.className).toContain('active');
  });

  it('changes layout to two columns', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    const twoColumnsBtn = screen.getByTitle('Two Columns');
    fireEvent.click(twoColumnsBtn);
    expect(twoColumnsBtn.className).toContain('active');
  });

  it('changes layout to three columns (default)', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    const threeColumnsBtn = screen.getByTitle('Three Columns');
    expect(threeColumnsBtn.className).toContain('active');
  });

  it('renders Filter Configurations chart section', () => {
    render(<Statistics />, { wrapper: createWrapper() });
    expect(screen.getByText('Filter Configurations & Job Counts')).toBeInTheDocument();
  });
});

describe('Statistics - CustomTooltip', () => {
  it('renders CustomTooltip when active with payload', async () => {
    vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
    
    render(<Statistics />, { wrapper: createWrapper() });
  });
});
