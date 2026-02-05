import { vi } from 'vitest';

export const mockJobsData = {
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
    refetch: vi.fn(),
};

export const mockJobSelection = {
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

export const mockJobMutations = {
    message: null,
    setMessage: vi.fn(),
    confirmModal: { isOpen: false, setConfirmModal: vi.fn() },
    setConfirmModal: vi.fn(),
    handleJobUpdate: vi.fn(),
    ignoreSelected: vi.fn(),
};
