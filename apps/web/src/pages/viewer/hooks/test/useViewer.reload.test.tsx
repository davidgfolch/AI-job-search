import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { useJobsData } from '../useJobsData';
import { useJobSelection } from '../useJobSelection';
import { useJobMutations } from '../useJobMutations';
import { mockJobsData, mockJobSelection, mockJobMutations } from './useViewer.mocks';

vi.mock('../useJobsData', () => ({
    useJobsData: vi.fn(),
}));
vi.mock('../useJobSelection', () => ({
    useJobSelection: vi.fn(),
}));
vi.mock('../useJobMutations', () => ({
    useJobMutations: vi.fn(),
}));
vi.mock('../../../common/hooks/useModalityValues', () => ({
    useModalityValues: vi.fn(),
}));

import { useModalityValues } from '../../../common/hooks/useModalityValues';

/** Re-applying the configuration already in effect leaves the query key untouched, so the list must be reloaded
 * from the current page instead. */
describe('useViewer reloadJobList', () => {
    const page1 = { items: [{ id: 1 }, { id: 2 }], page: 1, total: 2 };

    beforeEach(() => {
        vi.clearAllMocks();
        (useJobSelection as any).mockReturnValue(mockJobSelection);
        (useJobMutations as any).mockReturnValue(mockJobMutations);
        (useModalityValues as any).mockReturnValue({ data: [] });
    });

    const renderViewer = (overrides = {}) => {
        const reloadCurrentPage = vi.fn();
        const jobsData = {
            ...mockJobsData,
            data: page1,
            isPlaceholderData: false,
            filters: { page: 1, search: 'Backend' },
            reloadCurrentPage,
            ...overrides,
        };
        (useJobsData as any).mockReturnValue(jobsData);
        return { jobsData, reloadCurrentPage, ...renderHook(() => useViewer()) };
    };

    it('reloads the current page without changing the filters', async () => {
        const { result, reloadCurrentPage, jobsData } = renderViewer();

        await act(async () => { await result.current.actions.reloadJobList(); });

        expect(reloadCurrentPage).toHaveBeenCalledTimes(1);
        expect(jobsData.setFilters).not.toHaveBeenCalled();
        expect(jobsData.hardRefresh).not.toHaveBeenCalled();
    });

    it('keeps the selected job while the reloaded page replaces the list', async () => {
        const setAllJobs = vi.fn();
        const { result, rerender, reloadCurrentPage } = renderViewer({ allJobs: page1.items, setAllJobs });
        setAllJobs.mockClear();

        await act(async () => { await result.current.actions.reloadJobList(); });
        expect(reloadCurrentPage).toHaveBeenCalledTimes(1);

        // The refetched page 1 arrives; it is not placeholder data, so it replaces the list
        const reloaded = { items: [{ id: 1 }, { id: 2 }, { id: 3 }], page: 1, total: 3 };
        (useJobsData as any).mockReturnValue({
            ...mockJobsData,
            data: reloaded,
            isPlaceholderData: false,
            filters: { page: 1, search: 'Backend' },
            allJobs: page1.items,
            setAllJobs,
            reloadCurrentPage: vi.fn(),
        });
        rerender();

        const updater = setAllJobs.mock.calls.map(call => call[0]).find(arg => typeof arg === 'function');
        expect(updater).toBeDefined();
        expect((updater as any)(page1.items)).toEqual(reloaded.items);
        expect(mockJobSelection.handleJobSelect).not.toHaveBeenCalled();
    });
});
