import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useJobsData } from '../useJobsData';
import { jobsApi, type Job, type JobListResponse } from '../../api/ViewerApi';

// Mock react-router-dom
const mockSearchParams = new URLSearchParams();
vi.mock('react-router-dom', () => ({
  useSearchParams: () => [mockSearchParams],
}));

vi.mock('../../api/ViewerApi', () => ({
  jobsApi: {
    getJobs: vi.fn(),
  },
  DEFAULT_FILTERS: {},
}));

vi.mock('../../constants', () => ({
  DEFAULT_FILTERS: { page: 1, size: 20, ai_enriched: true, ignored: false },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useJobsData reload', () => {
  it('refetches the current query on reload, even while its data is fresh', async () => {
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [{ id: 1 } as Job], total: 100, page: 1, size: 20 });
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.data?.total).toBe(100));

    vi.mocked(jobsApi.getJobs).mockClear();
    const refreshed = { items: [{ id: 1 }, { id: 2 }], total: 101, page: 1, size: 20 };
    vi.mocked(jobsApi.getJobs).mockResolvedValueOnce(refreshed as unknown as JobListResponse);

    await act(async () => { await result.current.reloadCurrentPage(); });

    // Same query key as the page already in the cache: re-fetched, not served from it
    expect(vi.mocked(jobsApi.getJobs).mock.calls[0][0]).toEqual(result.current.filters);
    await waitFor(() => expect(result.current.data?.total).toBe(101));
  });

  it('leaves the cache of other filter sets untouched on reload', async () => {
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [{ id: 1 } as Job], total: 100, page: 1, size: 20 });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(() => useJobsData(), { wrapper });
    await waitFor(() => expect(result.current.data?.total).toBe(100));

    // A different filter set resolved earlier, as loading another configuration leaves it in the cache
    const otherKey = ['jobs', { page: 1, sql_filter: 'other' }];
    await act(async () => {
      await queryClient.prefetchQuery({ queryKey: otherKey, queryFn: () => Promise.resolve({ items: [], total: 7, page: 1, size: 20 }) });
    });
    const otherFetchedAt = queryClient.getQueryState(otherKey)?.dataUpdatedAt;
    vi.mocked(jobsApi.getJobs).mockClear();

    await act(async () => { await result.current.reloadCurrentPage(); });

    // Only the observed query was refetched; a cache reset (as hardRefresh does) would have refetched this one too
    expect(vi.mocked(jobsApi.getJobs).mock.calls.map(([params]) => params)).toEqual([result.current.filters]);
    expect(queryClient.getQueryState(otherKey)?.dataUpdatedAt).toBe(otherFetchedAt);
  });
});
