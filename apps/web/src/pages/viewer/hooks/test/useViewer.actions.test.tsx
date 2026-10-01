import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { useJobsData } from '../useJobsData';
import { useJobSelection } from '../useJobSelection';
import { useJobMutations } from '../useJobMutations';
import { useModalityValues } from '../../../common/hooks/useModalityValues';

/**
 * Every hook mock returns the *same* vi.fn() instances on each render. A factory
 * returning fresh fns per call would make the closures captured by `actions`
 * and the assertions read different instances, so effects would look uncalled.
 */
const mocks = vi.hoisted(() => ({
    selectionConfig: null as { onLoadMore: () => void } | null,
    mutationsConfig: null as any,
    appliedModalConfig: null as any,
    getJob: vi.fn(),
    selectedIds: new Set<number>(),
    selectionMode: 'manual' as string,
    setSelectedJob: vi.fn(), setSelectedIds: vi.fn(), setSelectionMode: vi.fn(),
    handleJobSelect: vi.fn(), navigateJob: vi.fn(),
    autoSelectNext: { current: {} as any },
    setMessage: vi.fn(), confirmClose: vi.fn(), handleJobUpdate: vi.fn(),
    ignoreSelected: vi.fn(), deleteSelected: vi.fn(), deleteSingleJob: vi.fn(),
    mutateAsync: vi.fn(), mutate: vi.fn(),
}));

vi.mock('../useJobsData', () => ({ useJobsData: vi.fn() }));
vi.mock('../useJobSelection', () => ({
    useJobSelection: vi.fn((config) => {
        mocks.selectionConfig = config;
        return {
            selectedJob: { id: 1 }, setSelectedJob: mocks.setSelectedJob,
            selectedIds: mocks.selectedIds, setSelectedIds: mocks.setSelectedIds,
            selectionMode: mocks.selectionMode, setSelectionMode: mocks.setSelectionMode,
            handleJobSelect: mocks.handleJobSelect, navigateJob: mocks.navigateJob,
            autoSelectNext: mocks.autoSelectNext,
        };
    }),
}));
vi.mock('../useJobMutations', () => ({
    useJobMutations: vi.fn((config) => {
        mocks.mutationsConfig = config;
        return {
            message: null, setMessage: mocks.setMessage, confirmModal: { isOpen: false, close: mocks.confirmClose },
            handleJobUpdate: mocks.handleJobUpdate, ignoreSelected: mocks.ignoreSelected,
            deleteSelected: mocks.deleteSelected, deleteSingleJob: mocks.deleteSingleJob,
            createMutation: { mutateAsync: mocks.mutateAsync }, bulkUpdateMutation: { mutate: mocks.mutate },
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
vi.mock('../../api/ViewerApi', () => ({ jobsApi: { getJob: (...args: unknown[]) => mocks.getJob(...args) } }));

const job = (over: Record<string, unknown> = {}) => ({ id: 1, company: 'Acme', ignored: false, seen: false, applied: false, discarded: false, closed: false, ...over });

const base = () => ({
    filters: { page: 1 }, setFilters: vi.fn(), allJobs: [job(), job({ id: 2 })], setAllJobs: vi.fn(),
    isLoadingMore: false, data: { total: 2, items: [job()], page: 1 }, isLoading: false, isPlaceholderData: false,
    error: null, handleLoadMore: vi.fn(), setIsLoadingMore: vi.fn(), hardRefresh: vi.fn(),
});

describe('useViewer actions and side effects', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mocks.selectedIds = new Set<number>();
        mocks.selectionMode = 'manual';
        mocks.autoSelectNext.current = {};
        (useModalityValues as any).mockReturnValue({ data: [] });
    });

    const renderViewer = (jobsData: ReturnType<typeof base> = base()) => {
        (useJobsData as any).mockReturnValue(jobsData);
        return { jobsData, ...renderHook(() => useViewer()) };
    };

    it('exposes state-change shortcuts that delegate to handleJobUpdate', () => {
        const { result } = renderViewer();
        act(() => { result.current.actions.ignoreJob(); result.current.actions.seenJob(); result.current.actions.discardedJob(); result.current.actions.closedJob(); });
        expect(mocks.handleJobUpdate).toHaveBeenNthCalledWith(1, { ignored: true });
        expect(mocks.handleJobUpdate).toHaveBeenNthCalledWith(2, { seen: true });
        expect(mocks.handleJobUpdate).toHaveBeenNthCalledWith(3, { discarded: true });
        expect(mocks.handleJobUpdate).toHaveBeenNthCalledWith(4, { closed: true });
        expect(result.current.actions.appliedJob).toBeTypeOf('function');
    });

    it('adds an unselected id and switches to manual selection', () => {
        const { result } = renderViewer();
        act(() => result.current.actions.toggleSelectJob(2));
        expect([...mocks.setSelectedIds.mock.calls[0][0]]).toEqual([2]);
        expect(mocks.setSelectionMode).toHaveBeenCalledWith('manual');
        expect(mocks.setSelectedJob).toHaveBeenCalledWith(expect.objectContaining({ id: 2 }));
    });

    it('adds an id that is not in the loaded list without changing the selection', () => {
        const { result } = renderViewer();
        act(() => result.current.actions.toggleSelectJob(7));
        expect([...mocks.setSelectedIds.mock.calls[0][0]]).toEqual([7]);
        expect(mocks.setSelectedJob).not.toHaveBeenCalled();
    });

    it('removes an already selected id, leaving select-all mode only when it was active', () => {
        mocks.selectedIds = new Set([7]);
        mocks.selectionMode = 'all';
        const { result, rerender } = renderViewer();
        rerender();
        act(() => result.current.actions.toggleSelectJob(7));
        expect([...mocks.setSelectedIds.mock.calls[0][0]]).toEqual([]);
        expect(mocks.setSelectionMode).toHaveBeenCalledWith('manual');
    });

    it('keeps select-all mode when deselecting a single id from manual mode', () => {
        mocks.selectedIds = new Set([7]);
        const { result, rerender } = renderViewer();
        rerender();
        act(() => result.current.actions.toggleSelectJob(7));
        expect(mocks.setSelectionMode).not.toHaveBeenCalled();
    });

    it('toggles between select-all and no selection', () => {
        const { result, rerender } = renderViewer();
        act(() => result.current.actions.toggleSelectAll());
        expect(mocks.setSelectionMode).toHaveBeenCalledWith('all');
        mocks.selectionMode = 'all';
        rerender();
        act(() => result.current.actions.toggleSelectAll());
        expect(mocks.setSelectionMode).toHaveBeenCalledWith('none');
        expect([...mocks.setSelectedIds.mock.calls[0][0]]).toEqual([]);
    });

    it('exposes an apiError until it is dismissed, then clears it', () => {
        const jobsData = base();
        jobsData.data = { ...jobsData.data, error: 'DB offline' } as any;
        const { result } = renderViewer(jobsData);
        expect(result.current.status.apiError).toBe('DB offline');
        act(() => result.current.actions.dismissMessage());
        expect(mocks.setMessage).toHaveBeenCalledWith(null);
        expect(result.current.status.apiError).toBeNull();
    });

    it('createJob persists, returns to the list and bumps the creation session', async () => {
        const jobsData = base();
        const { result } = renderViewer(jobsData);
        await act(async () => { await result.current.actions.createJob({ company: 'New' }); });
        expect(mocks.mutateAsync).toHaveBeenCalledWith({ company: 'New' });
        expect(result.current.state.activeTab).toBe('list');
        expect(result.current.state.creationSessionId).toBe(1);
        expect(jobsData.setFilters).toHaveBeenCalled();
    });

    it('refreshJobs hard-refreshes on page 1 and resets the page otherwise', async () => {
        const page1 = base();
        const onPage1 = renderViewer(page1).result;
        await act(async () => { await onPage1.current.actions.refreshJobs(); });
        expect(page1.hardRefresh).toHaveBeenCalled();
        expect(page1.setFilters).not.toHaveBeenCalled();

        const deeper = { ...base(), filters: { page: 4 } };
        const onDeeper = renderViewer(deeper).result;
        await act(async () => { await onDeeper.current.actions.refreshJobs(); });
        expect(deeper.hardRefresh).not.toHaveBeenCalled();
        expect(deeper.setFilters).toHaveBeenCalled();
    });

    it('selects the first job of the loaded page after a refresh', async () => {
        const { result } = renderViewer();
        await act(async () => { await result.current.actions.refreshJobs(); });
        await waitFor(() => expect(mocks.handleJobSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 1 })));
    });

    it('loads the duplicated job and closes it again', async () => {
        mocks.getJob.mockResolvedValue(job({ id: 42, company: 'Dup' }));
        const { result } = renderViewer();
        await act(async () => { await result.current.actions.openDuplicatedJob(42); });
        expect(mocks.getJob).toHaveBeenCalledWith(42);
        expect(result.current.state.duplicatedJob).toEqual(job({ id: 42, company: 'Dup' }));
        act(() => result.current.actions.closeDuplicatedJob());
        expect(result.current.state.duplicatedJob).toBeNull();
    });

    it('swallows and logs a duplicated-job load failure', async () => {
        const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
        mocks.getJob.mockRejectedValue(new Error('404'));
        const { result } = renderViewer();
        await act(async () => { await result.current.actions.openDuplicatedJob(9); });
        expect(result.current.state.duplicatedJob).toBeNull();
        expect(consoleError).toHaveBeenCalledWith('Failed to load duplicated job', expect.any(Error));
        consoleError.mockRestore();
    });
});