import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { useJobMutations } from '../useJobMutations';
import { jobsApi } from '../../api/ViewerApi';

vi.mock('../../api/ViewerApi', () => ({
  jobsApi: {
    updateJob: vi.fn(),
    bulkUpdateJobs: vi.fn(),
    deleteJobs: vi.fn(),
    createJob: vi.fn(),
  },
}));

vi.mock('../../../common/hooks/useConfirmationModal', () => ({
  useConfirmationModal: vi.fn(() => ({
    isOpen: false,
    message: '',
    close: vi.fn(),
    confirm: vi.fn((_msg: string, onConfirm: () => void) => onConfirm()),
    handleConfirm: vi.fn(),
  })),
}));

let client: QueryClient;

const makeProps = (overrides: Record<string, unknown> = {}) => ({
  filters: {},
  allJobs: [],
  selectedJob: null,
  setSelectedJob: vi.fn(),
  activeTab: 'list',
  autoSelectNext: { current: { shouldSelect: false, previousJobId: null } },
  selectedIds: new Set<number>(),
  setSelectedIds: vi.fn(),
  selectionMode: 'all',
  setSelectionMode: vi.fn(),
  ...overrides,
});

const createWrapper = () => {
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
};

describe('useJobMutations - select_all ignore refreshes list', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('invalidates the ["jobs"] query on a select_all ignore', async () => {
    vi.mocked(jobsApi.bulkUpdateJobs).mockResolvedValue({ updated: 3 });
    const wrapper = createWrapper();

    client.setQueryData(['jobs', {}], { items: [{ id: 1 }, { id: 2 }, { id: 3 }], total: 3 });

    const probe = () => {
      const { data } = useQuery({
        queryKey: ['jobs', {}],
        queryFn: async () => ({ items: [], total: 0 }),
      });
      return data;
    };
    const { result: probeResult } = renderHook(probe, { wrapper });
    expect(probeResult.current?.total).toBe(3);

    const { result } = renderHook(() => useJobMutations(makeProps()), { wrapper });
    await act(async () => result.current.ignoreSelected());

    await waitFor(() => expect(probeResult.current?.total).toBe(0));
    expect(jobsApi.bulkUpdateJobs).toHaveBeenCalledWith({
      select_all: true,
      filters: {},
      update: { ignored: true },
    });
  });
});
