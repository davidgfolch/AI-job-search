import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useJobMutations, getDeleteOldJobsMsg } from '../useJobMutations';
import { createWrapper, createDefaultJobMutationsProps } from '../../../test/ViewerTestUtils';

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
        confirm: vi.fn(),
        handleConfirm: vi.fn(),
    })),
}));

vi.mock('./useBulkJobMutations', () => ({
    useBulkJobMutations: vi.fn(() => ({
        bulkUpdateMutation: { mutate: vi.fn(), mutateAsync: vi.fn().mockResolvedValue({}) },
        bulkDeleteMutation: { mutate: vi.fn(), mutateAsync: vi.fn().mockResolvedValue({}) },
    })),
}));

import { jobsApi } from '../../api/ViewerApi';

describe('useJobMutations - additional tests', () => {
    let defaultProps: ReturnType<typeof createDefaultJobMutationsProps>;

    beforeEach(() => {
        vi.clearAllMocks();
        defaultProps = createDefaultJobMutationsProps();
    });

    it('should get delete old jobs message', () => {
        expect(getDeleteOldJobsMsg(5)).toBe('Going to delete 5 older jobs (see sql filter)');
    });

    it('should get delete old jobs message with zero count', () => {
        expect(getDeleteOldJobsMsg(0)).toBe('Going to delete 0 older jobs (see sql filter)');
    });

    it('should get delete old jobs message with large count', () => {
        expect(getDeleteOldJobsMsg(1000)).toBe('Going to delete 1000 older jobs (see sql filter)');
    });

    it('should return message state', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        expect(result.current.message).toBeNull();
    });

    it('should return confirmModal state', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        expect(result.current.confirmModal).toBeDefined();
    });

    it('should handle setMessage', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        
        act(() => {
            result.current.setMessage({ text: 'Test message', type: 'success' });
        });

        expect(result.current.message).toEqual({ text: 'Test message', type: 'success' });
    });

    it('should clear message', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        
        act(() => {
            result.current.setMessage({ text: 'Test message', type: 'success' });
        });
        
        act(() => {
            result.current.setMessage(null);
        });

        expect(result.current.message).toBeNull();
    });

    it('should return updateMutation', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        expect(result.current.updateMutation).toBeDefined();
    });

    it('should return createMutation', () => {
        const { result } = renderHook(() => useJobMutations(defaultProps), { wrapper: createWrapper() });
        expect(result.current.createMutation).toBeDefined();
    });
});
