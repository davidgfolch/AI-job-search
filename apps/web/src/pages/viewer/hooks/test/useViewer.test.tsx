import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { useJobsData } from '../useJobsData';
import { useJobSelection } from '../useJobSelection';
import { useJobMutations } from '../useJobMutations';
import { mockJobsData, mockJobSelection, mockJobMutations } from './useViewer.mocks';

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

describe('useViewer', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useJobsData as any).mockReturnValue(mockJobsData);
        (useJobSelection as any).mockReturnValue(mockJobSelection);
        (useJobMutations as any).mockReturnValue(mockJobMutations);
    });

    it('should aggregate state correctly', () => {
        const { result } = renderHook(() => useViewer());
        expect(result.current.state.filters).toEqual(mockJobsData.filters);
        expect(result.current.state.allJobs).toEqual(mockJobsData.allJobs);
        expect(result.current.state.selectedJob).toEqual(mockJobSelection.selectedJob);
        expect(result.current.state.activeTab).toBe('list');
    });

    it('should derive hasNext and hasPrevious correctly', () => {
        const { result } = renderHook(() => useViewer());
        expect(result.current.status.hasNext).toBe(true);
        expect(result.current.status.hasPrevious).toBe(false);
        
        (useJobSelection as any).mockReturnValue({
            ...mockJobSelection,
            selectedJob: { id: 2 },
        });
        const { result: result2 } = renderHook(() => useViewer());
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
        act(() => { result.current.actions.toggleSelectJob(2); });
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('manual');
        expect(mockJobSelection.setSelectedIds).toHaveBeenCalled();
        expect(mockJobSelection.setSelectedIds.mock.calls[0][0].has(2)).toBe(true);
    });

    it('should handle onJobsDeleted("all") correctly', () => {
        renderHook(() => useViewer());
        const useJobMutationsMock = useJobMutations as any;
        const onJobsDeleted = useJobMutationsMock.mock.calls[0][0].onJobsDeleted;
        expect(onJobsDeleted).toBeDefined();
        
        act(() => { onJobsDeleted('all'); });
        
        expect(mockJobsData.setAllJobs).toHaveBeenCalledWith([]); 
        expect(mockJobsData.setFilters).toHaveBeenCalled();
        const setFiltersUpdate = mockJobsData.setFilters.mock.calls[0][0];
        expect(setFiltersUpdate({}).page).toBe(1);
    });

    it('should handle toggleSelectAll correctly', () => {
        // Case 1: selectionMode is 'all' -> toggle off
        (useJobSelection as any).mockReturnValue({ ...mockJobSelection, selectionMode: 'all' });
        const { result } = renderHook(() => useViewer());
        act(() => { result.current.actions.toggleSelectAll(); });
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('none');
        expect(mockJobSelection.setSelectedIds).toHaveBeenCalledWith(new Set());
        
         // Case 2: selectionMode is 'none' -> toggle on
        (useJobSelection as any).mockReturnValue({ ...mockJobSelection, selectionMode: 'none' });
        const { result: result2 } = renderHook(() => useViewer());
         act(() => { result2.current.actions.toggleSelectAll(); });
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('all');
    });

    it('should refresh jobs when calling refreshJobs action', async () => {
        renderHook(() => useViewer());
        mockJobsData.setFilters.mockClear();
        const refetch = vi.fn().mockResolvedValue({ data: { items: [{ id: 99 }] } });
        const hardRefresh = vi.fn();
        (useJobsData as any).mockReturnValue({ ...mockJobsData, refetch, hardRefresh });
        
        const { result: result2 } = renderHook(() => useViewer());
        
        // Case 1: Page is not 1 -> reset page
        result2.current.state.filters.page = 2;
        await act(async () => { await result2.current.actions.refreshJobs(); });
        expect(mockJobsData.setFilters).toHaveBeenCalled(); 

        // Case 2: Page is 1 -> refetch
        result2.current.state.filters.page = 1;
        mockJobsData.setFilters.mockClear();
        await act(async () => { await result2.current.actions.refreshJobs(); });
        expect(hardRefresh).toHaveBeenCalled();
    });

    it('should NOT update allJobs or reset visible loading state if data is stale (page mismatch)', () => {
        const mockSetAllJobs = vi.fn();
        const mockSetIsLoadingMore = vi.fn();

        (useJobsData as any).mockReturnValue({
            ...mockJobsData,
            filters: { page: 2 },
            data: { items: [{ id: 100 }], page: 1 }, 
            setAllJobs: mockSetAllJobs,
            setIsLoadingMore: mockSetIsLoadingMore,
        });

        renderHook(() => useViewer());
        
        expect(mockSetAllJobs).not.toHaveBeenCalled();
        expect(mockSetIsLoadingMore).not.toHaveBeenCalled();
    });

    it('should update allJobs when fresh data arrives', () => {
        const mockSetAllJobs = vi.fn();
        const mockSetIsLoadingMore = vi.fn();

        (useJobsData as any).mockReturnValue({
            ...mockJobsData,
            filters: { page: 2 },
            data: { items: [{ id: 200 }], page: 2 },
            setAllJobs: mockSetAllJobs,
            setIsLoadingMore: mockSetIsLoadingMore,
        });

        renderHook(() => useViewer());

        expect(mockSetAllJobs).toHaveBeenCalled();
        expect(mockSetIsLoadingMore).toHaveBeenCalledWith(false);
    });
});
