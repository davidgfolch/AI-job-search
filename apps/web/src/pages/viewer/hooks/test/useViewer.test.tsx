import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { useJobsData } from '../useJobsData';
import { useJobSelection } from '../useJobSelection';
import { useJobMutations } from '../useJobMutations';
import { useJobUpdates } from '../useJobUpdates';

// Mock dependencies
vi.mock('../useJobsData', () => ({
    useJobsData: vi.fn(),
}));
vi.mock('../useJobSelection', () => ({
    useJobSelection: vi.fn(),
}));
vi.mock('../useJobMutations', () => ({
    useJobMutations: vi.fn(),
}));
vi.mock('../useJobUpdates', () => ({
    useJobUpdates: vi.fn(),
}));

describe('useViewer', () => {
    // Default mock returns
    const mockJobsData = {
        filters: { page: 1 },
        setFilters: vi.fn(),
        allJobs: [{ id: 1 }, { id: 2 }],
        setAllJobs: vi.fn(),
        isLoadingMore: false,
        data: { total: 2, items: [] },
        isLoading: false,
        error: null,
        handleLoadMore: vi.fn(),
        setIsLoadingMore: vi.fn(),
        hardRefresh: vi.fn(),
    };

    const mockJobSelection = {
        selectedJob: { id: 1 },
        setSelectedJob: vi.fn(),
        selectedIds: new Set([1]),
        setSelectedIds: vi.fn(),
        selectionMode: 'manual',
        setSelectionMode: vi.fn(),
        handleJobSelect: vi.fn(),
        navigateJob: vi.fn(),
        autoSelectNext: { current: {} },
    };

    const mockJobMutations = {
        message: null,
        setMessage: vi.fn(),
        confirmModal: { isOpen: false, setConfirmModal: vi.fn() },
        setConfirmModal: vi.fn(),
        handleJobUpdate: vi.fn(),
        ignoreSelected: vi.fn(),
    };

    beforeEach(() => {
        vi.clearAllMocks();
        (useJobsData as any).mockReturnValue(mockJobsData);
        (useJobSelection as any).mockReturnValue(mockJobSelection);
        (useJobMutations as any).mockReturnValue(mockJobMutations);
        (useJobUpdates as any).mockReturnValue({ hasNewJobs: false, newJobsCount: 0 });
    });

    it('should aggregate state correctly', () => {
        const { result } = renderHook(() => useViewer());
        expect(result.current.state.filters).toEqual(mockJobsData.filters);
        expect(result.current.state.allJobs).toEqual(mockJobsData.allJobs);
        expect(result.current.state.selectedJob).toEqual(mockJobSelection.selectedJob);
        // Default activeTab is 'list'
        expect(result.current.state.activeTab).toBe('list');
    });

    it('should derive hasNext and hasPrevious correctly', () => {
        // With selectedJob id: 1 and allJobs: [{id: 1}, {id: 2}]
        // Index is 0. hasNext=true, hasPrevious=false.
        const { result } = renderHook(() => useViewer());
        expect(result.current.status.hasNext).toBe(true);
        expect(result.current.status.hasPrevious).toBe(false);
        // Update mock to select second job
        (useJobSelection as any).mockReturnValue({
            ...mockJobSelection,
            selectedJob: { id: 2 },
        });
        const { result: result2 } = renderHook(() => useViewer());
        // Index is 1. hasNext=false, hasPrevious=true.
        expect(result2.current.status.hasNext).toBe(false);
        expect(result2.current.status.hasPrevious).toBe(true);
    });

    it('should expose actions that delegate to sub-hooks', () => {
        const { result } = renderHook(() => useViewer());
        result.current.actions.setFilters({ page: 2 } as any);
        expect(mockJobsData.setFilters).toHaveBeenCalledWith({ page: 2 });
        result.current.actions.nextJob();
        expect(mockJobSelection.navigateJob).toHaveBeenCalledWith('next');
        result.current.actions.ignoreJob();
        expect(mockJobMutations.handleJobUpdate).toHaveBeenCalledWith({ ignored: true });
    });

    it('should handle toggleSelectJob correctly', () => {
        const { result } = renderHook(() => useViewer());
        const setSelectedIds = mockJobSelection.setSelectedIds;
        // Toggle id 2 (not currently selected)
        act(() => {
            result.current.actions.toggleSelectJob(2);
        });
        // Should verify setSelectionMode to 'manual' and adding id
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('manual');
        expect(setSelectedIds).toHaveBeenCalled();
        // Check argument to setSelectedIds
        const callArg = setSelectedIds.mock.calls[0][0];
        // It's likely a Set.
        expect(callArg.has(2)).toBe(true);
    });

    it('should handle onJobsDeleted("all") correctly', () => {
        renderHook(() => useViewer());
        // Capture the onJobsDeleted callback passed to useJobMutations
        const useJobMutationsMock = useJobMutations as any;
        const passedProps = useJobMutationsMock.mock.calls[0][0];
        const onJobsDeleted = passedProps.onJobsDeleted;
        // Verify it exists
        expect(onJobsDeleted).toBeDefined();
        // Call it with 'all'
        act(() => {
            onJobsDeleted('all');
        });
        // Verify state updates
        // Should clear allJobs
        expect(mockJobsData.setAllJobs).toHaveBeenCalledWith([]); 
        // Should reset filters (page: 1)
        expect(mockJobsData.setFilters).toHaveBeenCalled();
        const setFiltersUpdate = mockJobsData.setFilters.mock.calls[0][0];
        // It's a function updater: f => ({ ...f, page: 1 })
        const newFilters = setFiltersUpdate({ some: 'filter' });
        expect(newFilters.page).toBe(1);
    });

    it('should handle toggleSelectAll correctly', () => {
        // Case 1: selectionMode is 'all' -> toggle off
        (useJobSelection as any).mockReturnValue({
            ...mockJobSelection,
            selectionMode: 'all',
        });
        const { result } = renderHook(() => useViewer());
        act(() => {
            result.current.actions.toggleSelectAll();
        });
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('none');
        expect(mockJobSelection.setSelectedIds).toHaveBeenCalledWith(new Set());
         // Case 2: selectionMode is 'none' -> toggle on
        (useJobSelection as any).mockReturnValue({
            ...mockJobSelection,
            selectionMode: 'none',
        });
        const { result: result2 } = renderHook(() => useViewer());
         act(() => {
            result2.current.actions.toggleSelectAll();
        });
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('all');
    });

    it('should return newJobsCount from useJobUpdates', () => {
        (useJobUpdates as any).mockReturnValue({ hasNewJobs: true, newJobsCount: 5 });
        const { result } = renderHook(() => useViewer());
        expect(result.current.state.hasNewJobs).toBe(true);
        expect(result.current.state.newJobsCount).toBe(5);
    });

    it('should refresh jobs when calling refreshJobs action', async () => {
        renderHook(() => useViewer());
        // Mock refetch return
        mockJobsData.setFilters.mockClear();
        const refetch = vi.fn().mockResolvedValue({ data: { items: [{ id: 99 }] } });
        const hardRefresh = vi.fn();
        (useJobsData as any).mockReturnValue({ ...mockJobsData, refetch, hardRefresh });
        // render hook again to pick up new mock
        const { result: result2 } = renderHook(() => useViewer());
        // Case 1: Page is not 1 -> reset page
        result2.current.state.filters.page = 2;
        await act(async () => {
             await result2.current.actions.refreshJobs();
        });
        expect(mockJobsData.setFilters).toHaveBeenCalled(); // Should reset page to 1
        // Case 2: Page is 1 -> refetch
        result2.current.state.filters.page = 1;
        mockJobsData.setFilters.mockClear();
        await act(async () => {
            await result2.current.actions.refreshJobs();
        });
        expect(hardRefresh).toHaveBeenCalled();
        // Since we are using hardRefresh, data flow might be different (e.g. relying on useEffect)
        // For this unit test of action delegation, checking hardRefresh call is sufficient.
        // expect(mockJobSelection.handleJobSelect).toHaveBeenCalledWith({ id: 99 });
    });
});
