import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useJobsData } from '../useJobsData';
import { jobsApi } from '../../api/ViewerApi';

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

describe('useJobsData', () => {
  it('initializes with default filters when no URL params', () => {
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [], total: 0, page: 1, size: 20 });
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    expect(result.current.filters).toEqual({ page: 1, size: 20, ai_enriched: true, ignored: false });
  });

  it('initializes filters from URL ids', () => {
    vi.spyOn(mockSearchParams, 'get').mockReturnValue('1,2,3');
    vi.mocked(jobsApi.getJobs).mockResolvedValue({ items: [], total: 0, page: 1, size: 20 });
    
    // We need to re-render hook to pick up new mock return value? 
    // Actually renderHook runs in isolation.
    // Ideally we should mock per test, but we defined mock globally.
    // Let's rely on the mock return value change before renderHook.
    
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    
    expect(result.current.filters).toEqual(expect.objectContaining({
        ids: [1, 2, 3],
        ai_enriched: undefined,
        ignored: undefined
    }));
    
    // Reset mock
    vi.spyOn(mockSearchParams, 'get').mockReturnValue(null);
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

  it('keeps previous data while fetching new page', async () => {
    const page1Data = { items: [{ id: 1, title: 'Job 1' }], total: 10, page: 1, size: 20 };
    const page2Data = { items: [{ id: 2, title: 'Job 2' }], total: 10, page: 2, size: 20 };
    
    // First call resolves immediately
    vi.mocked(jobsApi.getJobs).mockResolvedValueOnce(page1Data as any);
    
    const { result } = renderHook(() => useJobsData(), { wrapper: createWrapper() });
    
    // Wait for page 1
    await waitFor(() => expect(result.current.data).toEqual(page1Data));
    
    // Second call will resolve delayed
    let resolvePage2: (value: any) => void;
    const page2Promise = new Promise(resolve => { resolvePage2 = resolve; });
    vi.mocked(jobsApi.getJobs).mockImplementationOnce(async () => {
        const val = await page2Promise;
        return val as any; 
    });

    // Trigger page change
    act(() => {
        result.current.setFilters(prev => ({ ...prev, page: 2 }));
    });

    // Check that we still have page 1 data (keepPreviousData behavior)
    expect(result.current.data).toEqual(page1Data);
    
    // Resolve page 2
    await act(async () => {
        resolvePage2!(page2Data);
    });
    
    await waitFor(() => expect(result.current.data).toEqual(page2Data));
  });
});

