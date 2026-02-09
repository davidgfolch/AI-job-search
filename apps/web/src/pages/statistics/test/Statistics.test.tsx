import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Statistics from '../Statistics';
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

describe('Statistics', () => {
  it('renders statistics page title', () => {
    vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
    render(<Statistics />, { wrapper: createWrapper() });
    expect(screen.getByText('AI Job Search - Statistics')).toBeInTheDocument();
  });

  it('renders all chart sections', () => {
    vi.mocked(StatisticsApi.getHistoryStats).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByDate).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByHour).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getSourcesByWeekday).mockResolvedValue([]);
    vi.mocked(StatisticsApi.getFilterConfigStats).mockResolvedValue([]);
    render(<Statistics />, { wrapper: createWrapper() });
    expect(screen.getByText('Applied vs Discarded Jobs (History)')).toBeInTheDocument();
    expect(screen.getByText('Job Postings by Source & Created Date')).toBeInTheDocument();
    expect(screen.getByText('Job Postings by Source & Day Time')).toBeInTheDocument();
    expect(screen.getByText('Job Postings by Source & Day of Week')).toBeInTheDocument();
  });
});
