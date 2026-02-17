import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobMutations } from '../useJobMutations';
import { jobsApi } from '../../api/ViewerApi';
import { createWrapper, createDefaultJobMutationsProps } from '../../../test/ViewerTestUtils';

vi.mock('../../api/ViewerApi', () => ({
    jobsApi: {
        updateJob: vi.fn(),
        bulkUpdateJobs: vi.fn(),
        deleteJobs: vi.fn(),
        createJob: vi.fn(),
    },
}));

// Mock useBulkJobMutations to avoid complex modal interaction
const mutationMocks = vi.hoisted(() => ({
    mockBulkUpdateMutation: { mutate: vi.fn() },
    mockBulkDeleteMutation: { mutate: vi.fn() }
}));

const { mockBulkUpdateMutation, mockBulkDeleteMutation } = mutationMocks;

vi.mock('../../../common/hooks/useConfirmationModal', () => ({
    useConfirmationModal: () => ({
        confirm: vi.fn((msg, cb) => cb()), // Auto-confirm for tests
        isOpen: false,
        message: '',
        handleConfirm: vi.fn(),
        close: vi.fn(),
    }),
}));

vi.mock('../useBulkJobMutations', () => ({
    useBulkJobMutations: () => {
        return {
            bulkUpdateMutation: mutationMocks.mockBulkUpdateMutation,
            bulkDeleteMutation: mutationMocks.mockBulkDeleteMutation
        };
    }
}));

describe('useJobMutations', () => {
    let defaultProps: ReturnType<typeof createDefaultJobMutationsProps>;

    beforeEach(() => {
        vi.clearAllMocks();
        defaultProps = createDefaultJobMutationsProps();
    });

    it('should initialize with default state', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        expect(result.current.message).toBeNull();
        expect(result.current.confirmModal.isOpen).toBe(false);
    });

    it('should handle single job update success', async () => {
        (jobsApi.updateJob as any).mockResolvedValue({ id: 1, title: 'Job 1 Updated', ignored: false });
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        await act(async () => {
            result.current.updateMutation.mutate({ id: 1, data: { title: 'New Title' } });
        });
        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { title: 'New Title' });
        expect(defaultProps.setSelectedJob).toHaveBeenCalledWith(expect.objectContaining({ title: 'Job 1 Updated' }));
    });

    it.each([
        { field: { ignored: true }, shouldSelect: true, desc: 'state field updated' },
        { field: { title: 'Updated' }, shouldSelect: false, desc: 'non-state field updated' }
    ])('autoSelectNext behavior when $desc', async ({ field, shouldSelect }) => {
        (jobsApi.updateJob as any).mockResolvedValue({ id: 1, ...field });
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        await act(async () => {
            result.current.handleJobUpdate(field as any);
        });
        expect(defaultProps.autoSelectNext.current.shouldSelect).toBe(shouldSelect);
    });

    it.each([
        { ids: [1, 2], mode: 'manual', method: 'ignoreSelected', api: 'bulkUpdateJobs', check: { update: { ignored: true } } },
        { ids: [1, 2, 3], mode: 'manual', method: 'deleteSelected', api: 'deleteJobs', count: 3, check: {} }, // delete uses ids directly in bulkDeleteMutation logic if mocked simply
    ])('should handle $method with confirmation ($mode)', async ({ ids, mode, method, api, count, check }) => {
        (jobsApi.bulkUpdateJobs as any).mockResolvedValue({ updated: ids.length });
        (jobsApi.deleteJobs as any).mockResolvedValue({ deleted: ids.length });
        const props = { ...defaultProps, selectedIds: new Set(ids), selectionMode: mode as any };
        const { result } = renderHook(() => useJobMutations(props), { wrapper: createWrapper() });
        
        await act(async () => {
             (result.current as any)[method](count);
        });

        // With auto-confirm mock and useBulkJobMutations mock:
        // confirm call -> cb() -> mutation.mutate(...)
        
        if (api === 'bulkUpdateJobs') {
             expect(mockBulkUpdateMutation.mutate).toHaveBeenCalledWith(expect.objectContaining({ ids, ...check }));
        } else {
             expect(mockBulkDeleteMutation.mutate).toHaveBeenCalled(); 
        }
    });

    it('should handle bulk actions with "all" selection mode', async () => {
         const props = { ...defaultProps, selectionMode: 'all' as const };
         const { result } = renderHook(() => useJobMutations(props), { wrapper: createWrapper() });         
         
         await act(async () => result.current.ignoreSelected());
         expect(mockBulkUpdateMutation.mutate).toHaveBeenCalledWith(expect.objectContaining({ select_all: true, update: { ignored: true } }));
         
         // Test delete all
         await act(async () => result.current.deleteSelected(100));
         expect(mockBulkDeleteMutation.mutate).toHaveBeenCalled(); 
    });

    it('should handle create job success', async () => {
        (jobsApi.createJob as any).mockResolvedValue({ id: 2, title: 'New Job' });
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        await act(async () => {
            await result.current.createMutation.mutateAsync({ title: 'New Job' });
        });
        expect(jobsApi.createJob).toHaveBeenCalledWith({ title: 'New Job' });
        await waitFor(() => {
             expect(result.current.createMutation.isSuccess).toBe(true);
        });
    });


});

