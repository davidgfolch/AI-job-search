import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useViewer } from '../useViewer';
import { useJobsData } from '../useJobsData';
import { useJobSelection } from '../useJobSelection';
import { useJobMutations } from '../useJobMutations';
import { useModalityValues } from '../../../common/hooks/useModalityValues';

/** Stable instances: the closures captured by the hook must be the ones asserted on. */
const mocks = vi.hoisted(() => ({
    selectionConfig: null as any, mutationsConfig: null as any, appliedModalConfig: null as any,
    setSelectedJob: vi.fn(), setSelectedIds: vi.fn(), setSelectionMode: vi.fn(),
    handleJobSelect: vi.fn(), navigateJob: vi.fn(), autoSelectNext: { current: {} as any },
    setMessage: vi.fn(), handleJobUpdate: vi.fn(), mutate: vi.fn(), mutateAsync: vi.fn(),
}));

vi.mock('../useJobsData', () => ({ useJobsData: vi.fn() }));
vi.mock('../useJobSelection', () => ({
    useJobSelection: vi.fn((config) => {
        mocks.selectionConfig = config;
        return {
            selectedJob: { id: 1 }, setSelectedJob: mocks.setSelectedJob,
            selectedIds: new Set<number>(), setSelectedIds: mocks.setSelectedIds,
            selectionMode: 'manual', setSelectionMode: mocks.setSelectionMode,
            handleJobSelect: mocks.handleJobSelect, navigateJob: mocks.navigateJob,
            autoSelectNext: mocks.autoSelectNext,
        };
    }),
}));
vi.mock('../useJobMutations', () => ({
    useJobMutations: vi.fn((config) => {
        mocks.mutationsConfig = config;
        return {
            message: null, setMessage: mocks.setMessage, confirmModal: { isOpen: false, close: vi.fn() },
            handleJobUpdate: mocks.handleJobUpdate, ignoreSelected: vi.fn(), deleteSelected: vi.fn(),
            deleteSingleJob: vi.fn(), createMutation: { mutateAsync: mocks.mutateAsync }, bulkUpdateMutation: { mutate: mocks.mutate },
        };
    }),
}));
vi.mock('../useAppliedModal', () => ({
    useAppliedModal: vi.fn((config) => {
        mocks.appliedModalConfig = config;
        return { isModalOpen: false, openModal: vi.fn(), handleConfirm: vi.fn(), handleCancel: vi.fn() };
    }),
}));
vi.mock('../../../common/hooks/useModalityValues', () => ({ useModalityValues: vi.fn() }));

const job = (id: number, over: Record<string, unknown> = {}) => ({ id, company: `C${id}`, ignored: false, seen: false, applied: false, discarded: false, closed: false, ...over });

const base = (over: Record<string, unknown> = {}) => ({
    filters: { page: 1, seen: false, ignored: false, applied: false, discarded: false, closed: false, ...over },
    setFilters: vi.fn(), allJobs: [job(1), job(2)], setAllJobs: vi.fn(), isLoadingMore: false,
    data: { total: 2, items: [job(1)], page: 1 }, isLoading: false, isPlaceholderData: false,
    error: null, handleLoadMore: vi.fn(), setIsLoadingMore: vi.fn(), hardRefresh: vi.fn(),
});

/** setAllJobs is mocked, so its updater never runs on its own: invoke it explicitly. */
const lastUpdater = (setAllJobs: any, from = 0) => {
    const calls = setAllJobs.mock.calls.slice(from).map((c: any[]) => c[0]).filter(a => typeof a === 'function');
    expect(calls.length).toBeGreaterThan(0);
    return calls.at(-1);
};

describe('useViewer data merging and callbacks', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mocks.autoSelectNext.current = {};
        (useModalityValues as any).mockReturnValue({ data: [] });
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    const renderViewer = (jobsData: ReturnType<typeof base> = base()) => {
        (useJobsData as any).mockReturnValue(jobsData);
        return renderHook(() => useViewer());
    };

    it('wires load-more to a variant that auto-selects the first new job', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.selectionConfig.onLoadMore());
        expect(jobsData.handleLoadMore).toHaveBeenCalled();
        expect(mocks.selectionConfig.hasMorePages).toBe(false);
    });

    it('appends page 2 items, ignoring duplicates, and auto-selects the first new one', () => {
        vi.useFakeTimers();
        const page2 = base({ page: 2 });
        page2.filters = { ...page2.filters, page: 2 } as any;
        page2.data = { total: 4, items: [job(2), job(3)], page: 2 } as any;
        renderViewer(page2);
        act(() => mocks.selectionConfig.onLoadMore());
        const merged = lastUpdater(page2.setAllJobs)([job(1), job(2)]);
        expect(merged).toEqual([job(1), job(2), job(3)]);
        act(() => { vi.runAllTimers(); });
        expect(mocks.handleJobSelect).toHaveBeenCalledWith(job(3));
    });

    it('keeps the accumulated jobs when the incoming page adds nothing new', () => {
        const page2 = base({ page: 2 });
        page2.filters = { ...page2.filters, page: 2 } as any;
        page2.data = { total: 2, items: [job(1), job(2)], page: 2 } as any;
        renderViewer(page2);
        expect(lastUpdater(page2.setAllJobs)([job(1), job(2)])).toEqual([job(1), job(2)]);
    });

    it('drops a job from the list when the update flips a filter state field', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.mutationsConfig.onJobUpdated(job(2, { seen: true })));
        expect(lastUpdater(jobsData.setAllJobs)([job(1), job(2)])).toEqual([job(1)]);
    });

    it('replaces the job in place when no filter state field changed', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.mutationsConfig.onJobUpdated(job(2, { company: 'Renamed' })));
        expect(lastUpdater(jobsData.setAllJobs)([job(1), job(2)])).toEqual([job(1), job(2, { company: 'Renamed' })]);
    });

    it('clears everything when all jobs are deleted', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.mutationsConfig.onJobsDeleted('all'));
        expect(jobsData.setAllJobs).toHaveBeenCalledWith([]);
        const filtersUpdater = jobsData.setFilters.mock.calls.map((c: any[]) => c[0]).find(a => typeof a === 'function');
        expect(filtersUpdater({ page: 7 })).toEqual({ page: 1 });
    });

    it('removes only the deleted ids', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.mutationsConfig.onJobsDeleted([1]));
        expect(lastUpdater(jobsData.setAllJobs)([job(1), job(2)])).toEqual([job(2)]);
    });

    it('arms auto-select for a single-job bulk update that changes a state field', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.appliedModalConfig.onBulkUpdate([2], { seen: true }));
        expect(mocks.autoSelectNext.current).toEqual({ shouldSelect: true, previousJobId: 2, previousJobIndex: 1 });
        expect(mocks.mutate).toHaveBeenCalledWith({ ids: [2], update: { seen: true } });
    });

    it('leaves the index undefined when the bulk-updated job is not loaded', () => {
        const jobsData = base();
        renderViewer(jobsData);
        act(() => mocks.appliedModalConfig.onBulkUpdate([99], { seen: true }));
        expect(mocks.autoSelectNext.current).toEqual({ shouldSelect: true, previousJobId: 99, previousJobIndex: undefined });
    });

    it.each([
        ['no state field changes', [2], { company: 'Renamed' }],
        ['more than one job', [1, 2], { seen: true }],
        ['no job selected', [], { seen: true }],
    ])('does not arm auto-select for a bulk update with %s', (_label, ids, update) => {
        renderViewer();
        act(() => mocks.appliedModalConfig.onBulkUpdate(ids as number[], update));
        expect(mocks.autoSelectNext.current).toEqual({});
        expect(mocks.mutate).toHaveBeenCalledWith({ ids, update });
    });

    it('does not arm auto-select outside the list tab', () => {
        const { result } = renderViewer();
        act(() => result.current.actions.setActiveTab('stats'));
        act(() => mocks.appliedModalConfig.onBulkUpdate([2], { seen: true }));
        expect(mocks.autoSelectNext.current).toEqual({});
        expect(mocks.mutate).toHaveBeenCalled();
    });
});