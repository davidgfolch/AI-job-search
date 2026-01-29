import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBulkJobMutations } from '../useBulkJobMutations';
import { jobsApi } from '../../api/ViewerApi';

vi.mock('../../api/ViewerApi', () => ({
  jobsApi: {
    bulkUpdateJobs: vi.fn(),
    deleteJobs: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useBulkJobMutations', () => {
  const mockProps = {
    onJobsDeleted: vi.fn(),
    setMessage: vi.fn(),
    setSelectionMode: vi.fn(),
    setSelectedIds: vi.fn(),
    onUpdateSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('bulkUpdateMutation', () => {
    it('updates jobs successfully', async () => {
      vi.mocked(jobsApi.bulkUpdateJobs).mockResolvedValue({ updated: 5 });
      const { result } = renderHook(() => useBulkJobMutations(mockProps), { wrapper: createWrapper() });
      result.current.bulkUpdateMutation.mutate({ ids: [1, 2], update: { flagged: true } });
      await waitFor(() => expect(result.current.bulkUpdateMutation.isSuccess).toBe(true));
      expect(mockProps.setMessage).toHaveBeenCalledWith({ text: 'Updated 5 jobs', type: 'success' });
      expect(mockProps.setSelectionMode).toHaveBeenCalledWith('none');
    });

    it('handles update errors', async () => {
      const error = new Error('Update failed');
      vi.mocked(jobsApi.bulkUpdateJobs).mockRejectedValue(error);
      const { result } = renderHook(() => useBulkJobMutations(mockProps), { wrapper: createWrapper() });
      result.current.bulkUpdateMutation.mutate({ ids: [1], update: {} });
      await waitFor(() => expect(result.current.bulkUpdateMutation.isError).toBe(true));
      expect(mockProps.setMessage).toHaveBeenCalledWith({ text: 'Update failed', type: 'error' });
    });
  });

  describe('bulkDeleteMutation', () => {
    it('deletes jobs successfully', async () => {
      vi.mocked(jobsApi.deleteJobs).mockResolvedValue({ deleted: 3 });
      const { result } = renderHook(() => useBulkJobMutations(mockProps), { wrapper: createWrapper() });
      result.current.bulkDeleteMutation.mutate({ ids: [1, 2, 3] });
      await waitFor(() => expect(result.current.bulkDeleteMutation.isSuccess).toBe(true));
      expect(mockProps.setMessage).toHaveBeenCalledWith({ text: 'Deleted 3 jobs', type: 'success' });
      expect(mockProps.onJobsDeleted).toHaveBeenCalledWith([1, 2, 3]);
    });

    it('handles delete errors', async () => {
      vi.mocked(jobsApi.deleteJobs).mockRejectedValue(new Error('Delete failed'));
      const { result } = renderHook(() => useBulkJobMutations(mockProps), { wrapper: createWrapper() });
      result.current.bulkDeleteMutation.mutate({ ids: [1] });
      await waitFor(() => expect(result.current.bulkDeleteMutation.isError).toBe(true));
      expect(mockProps.setMessage).toHaveBeenCalledWith({ text: 'Delete failed', type: 'error' });
    });
  });
});
