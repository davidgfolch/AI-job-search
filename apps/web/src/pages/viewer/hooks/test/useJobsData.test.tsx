import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useJobsData } from '../useJobsData';
import { jobsApi } from '../../api/ViewerApi';

vi.mock('../../api/ViewerApi', () => ({
  jobsApi: {
    getJobs: vi.fn(),
  },
  DEFAULT_FILTERS: {},
}));

vi.mock('../../constants', () => ({
  DEFAULT_FILTERS: { page: 1, size: 20 },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useJobsData', () => {
  it('initializes with default filters', () => {
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [], total: 0, page: 1, size: 20 });
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    expect(result.current.filters).toEqual({ page: 1, size: 20 });
  });

  it('fetches jobs data', async () => {
    const mockData = { items: [{ id: 1, title: 'Test' }], total: 1, page: 1, size: 20 };
    vi.mocked(jobsApi.getJobs).mockResolvedValue(mockData as any);
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.data).toEqual(mockData));
  });

  it('loads more jobs when called', async () => {
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [], total: 100, page: 1, size: 20 });
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    
    await waitFor(() => expect(result.current.data?.total).toBe(100)); // Wait for data load

    act(() => {
        result.current.handleLoadMore();
    });
    
    expect(result.current.isLoadingMore).toBe(true);
  });

  it('resets queries on hard refresh', async () => {
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [], total: 0, page: 1, size: 20 });
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    await result.current.hardRefresh();
    expect(jobsApi.getJobs).toHaveBeenCalled();
  });
});
