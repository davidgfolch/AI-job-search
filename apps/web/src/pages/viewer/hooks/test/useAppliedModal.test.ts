import { renderHook, act } from '@testing-library/react';
import { useAppliedModal } from '../useAppliedModal';
import { type Job } from '../../api/ViewerApi';

// Mock the jobsApi
vi.mock('../../api/ViewerApi', () => ({
    jobsApi: {
        getJob: vi.fn(),
    },
}));

describe('useAppliedModal', () => {
    const mockSelectedJob: Job = {
        id: 1,
        title: 'Test Job',
        company: 'Test Company',
        comments: null,
        applied: false,
        // ... other required fields
        salary: null,
        location: null,
        url: null,
        markdown: null,
        web_page: null,
        created: '2023-01-01',
        modified: null,
        flagged: false,
        like: false,
        ignored: false,
        seen: false,
        discarded: false,
        closed: false,
        client: null,
        required_technologies: null,
        optional_technologies: null,
        ai_enriched: false,
        ai_enrich_error: null,
        duplicated_id: null,
    };

    const mockProps = {
        selectedJob: mockSelectedJob,
        allJobs: [mockSelectedJob],
        onJobUpdate: vi.fn(),
        onBulkUpdate: vi.fn(),
        selectedIds: new Set<number>(),
        selectionMode: 'none' as const,
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should start with modal closed', () => {
        const { result } = renderHook(() => useAppliedModal(mockProps));

        expect(result.current.isModalOpen).toBe(false);
    });

    it('should open modal for single job mode', () => {
        const { result } = renderHook(() => useAppliedModal(mockProps));

        act(() => {
            result.current.openModal();
        });

        expect(result.current.isModalOpen).toBe(true);
    });

    it('should open modal for single selection in bulk mode', () => {
        const props = {
            ...mockProps,
            selectionMode: 'manual' as const,
            selectedIds: new Set([1]),
        };

        const { result } = renderHook(() => useAppliedModal(props));

        act(() => {
            result.current.openModal();
        });

        expect(result.current.isModalOpen).toBe(true);
    });

    it('should not open modal for multiple selection', () => {
        const props = {
            ...mockProps,
            selectionMode: 'manual' as const,
            selectedIds: new Set([1, 2]),
        };

        const { result } = renderHook(() => useAppliedModal(props));

        act(() => {
            result.current.openModal();
        });

        expect(result.current.isModalOpen).toBe(false);
    });

    it('should not open modal for "all" selection', () => {
        const props = {
            ...mockProps,
            selectionMode: 'all' as const,
        };

        const { result } = renderHook(() => useAppliedModal(props));

        act(() => {
            result.current.openModal();
        });

        expect(result.current.isModalOpen).toBe(false);
    });

    it('should handle single job confirmation with comment', async () => {
        const { result } = renderHook(() => useAppliedModal(mockProps));

        act(() => {
            result.current.openModal();
        });

        const comment = '- applied with comment';
        await act(async () => {
            await result.current.handleConfirm(true, comment);
        });

        expect(mockProps.onJobUpdate).toHaveBeenCalledWith({
            applied: true,
            comments: '- applied with comment',
        });
        expect(result.current.isModalOpen).toBe(false);
    });

    it('should handle single job confirmation without comment', async () => {
        const { result } = renderHook(() => useAppliedModal(mockProps));

        act(() => {
            result.current.openModal();
        });

        await act(async () => {
            await result.current.handleConfirm(false, '');
        });

        expect(mockProps.onJobUpdate).toHaveBeenCalledWith({
            applied: true,
        });
        expect(result.current.isModalOpen).toBe(false);
    });

    it('should append comment to existing comments for single job', async () => {
        const jobWithExistingComment = {
            ...mockSelectedJob,
            comments: 'existing comment',
        };

        const props = {
            ...mockProps,
            selectedJob: jobWithExistingComment,
        };

        const { result } = renderHook(() => useAppliedModal(props));

        act(() => {
            result.current.openModal();
        });

        const newComment = '- applied with new comment';
        await act(async () => {
            await result.current.handleConfirm(true, newComment);
        });

        expect(mockProps.onJobUpdate).toHaveBeenCalledWith({
            applied: true,
            comments: 'existing comment - applied with new comment',
        });
    });

    it('should handle bulk confirmation with comment', async () => {
        const props = {
            ...mockProps,
            selectedJob: null, // No single job selected
            selectionMode: 'manual' as const,
            selectedIds: new Set([1]),
        };

        const { result } = renderHook(() => useAppliedModal(props));

        act(() => {
            result.current.openModal();
        });

        const comment = '- bulk applied';
        await act(async () => {
            await result.current.handleConfirm(true, comment);
        });

        expect(mockProps.onBulkUpdate).toHaveBeenCalledWith([1], {
            applied: true,
            comments: '- bulk applied',
        });
        expect(result.current.isModalOpen).toBe(false);
    });

    it('should handle cancellation', () => {
        const { result } = renderHook(() => useAppliedModal(mockProps));

        act(() => {
            result.current.openModal();
        });

        act(() => {
            result.current.handleCancel();
        });

        expect(result.current.isModalOpen).toBe(false);
    });

    it('should close modal after confirmation', async () => {
        const { result } = renderHook(() => useAppliedModal(mockProps));

        act(() => {
            result.current.openModal();
        });

        expect(result.current.isModalOpen).toBe(true);

        await act(async () => {
            await result.current.handleConfirm(true, 'test comment');
        });

        expect(result.current.isModalOpen).toBe(false);
    });
});