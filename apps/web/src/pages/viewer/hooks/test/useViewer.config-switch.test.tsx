import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useViewer } from '../useViewer';
import { useJobsData } from '../useJobsData';
import { useJobSelection } from '../useJobSelection';
import { useJobMutations } from '../useJobMutations';
import { mockJobsData, mockJobSelection, mockJobMutations } from './useViewer.mocks';
import type { Job } from '../../api/ViewerApi';

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

const setJobsData = (value: object) => vi.mocked(useJobsData).mockReturnValue(value as unknown as ReturnType<typeof useJobsData>);
const setJobSelection = (value: object) => vi.mocked(useJobSelection).mockReturnValue(value as unknown as ReturnType<typeof useJobSelection>);
const setJobMutations = (value: object) => vi.mocked(useJobMutations).mockReturnValue(value as unknown as ReturnType<typeof useJobMutations>);
const setModalityValues = (value: object) => vi.mocked(useModalityValues).mockReturnValue(value as unknown as ReturnType<typeof useModalityValues>);

describe('useViewer regression', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        setJobsData(mockJobsData);
        setJobSelection(mockJobSelection);
        setJobMutations(mockJobMutations);
        setModalityValues({ data: [] });
    });

    it('regression: list is replaced with the new config jobs after a config switch (placeholder data ignored)', () => {
        const mockSetAllJobs = vi.fn();
        const cleanData = { items: [{ id: 1 }], page: 1, total: 1 };
        const jvmData = { items: [{ id: 200 }], page: 1, total: 1 };

        setJobsData({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'clean', page: 1 },
            data: cleanData,
            isPlaceholderData: false,
            allJobs: cleanData.items,
            setAllJobs: mockSetAllJobs,
        });

        const { rerender } = renderHook(() => useViewer());
        mockSetAllJobs.mockClear();

        // Another config is clicked: previous data is shown as placeholder while fetching
        setJobsData({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'jvm', page: 1 },
            data: cleanData,
            isPlaceholderData: true,
            allJobs: [],
            setAllJobs: mockSetAllJobs,
        });
        rerender();

        // The config change resets the list and stale (placeholder) data is never written
        expect(mockSetAllJobs).toHaveBeenCalledWith([]);
        expect(mockSetAllJobs.mock.calls.some(([arg]) => typeof arg === 'function')).toBe(false);

        // The new config's real page-1 result arrives and replaces the list
        setJobsData({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'jvm', page: 1 },
            data: jvmData,
            isPlaceholderData: false,
            allJobs: [],
            setAllJobs: mockSetAllJobs,
        });
        rerender();

        const updater = mockSetAllJobs.mock.calls.map(call => call[0]).find((arg): arg is (jobs: Job[]) => Job[] => typeof arg === 'function')!;
        expect(updater).toBeDefined();
        expect(updater([])).toEqual(jvmData.items);
    });

    it('regression: auto-select-all is driven by filters.auto_select_all and not by the config name', () => {
        const mockSetAllJobs = vi.fn();
        const cleanData = { items: [{ id: 1 }], page: 1, total: 1 };
        const jvmData = { items: [{ id: 200 }], page: 1, total: 1 };

        // A configuration with auto_select_all selects every matching job as soon as its page-1 data is shown.
        setJobsData({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'clean', page: 1, auto_select_all: true },
            data: cleanData,
            isPlaceholderData: false,
            allJobs: cleanData.items,
            setAllJobs: mockSetAllJobs,
        });

        const { rerender } = renderHook(() => useViewer());
        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('all');

        // Manually deselecting is respected until the next configuration/filter change.
        mockJobSelection.setSelectionMode.mockClear();
        setJobSelection({ ...mockJobSelection, selectionMode: 'none' });
        rerender();
        expect(mockJobSelection.setSelectionMode).not.toHaveBeenCalledWith('all');

        // Switching to a configuration without the flag never selects all.
        setJobSelection({ ...mockJobSelection, selectionMode: 'manual' });
        setJobsData({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'jvm', page: 1 },
            data: jvmData,
            isPlaceholderData: false,
            allJobs: jvmData.items,
            setAllJobs: mockSetAllJobs,
        });
        rerender();
        expect(mockJobSelection.setSelectionMode).not.toHaveBeenCalledWith('all');
    });

    it('auto-selects all when the pill is toggled on with data already loaded', () => {
        const jvmData = { items: [{ id: 200 }], page: 1, total: 1 };
        const baseFilters = { ...mockJobsData.filters, sql_filter: 'jvm', page: 1 };

        setJobsData({
            ...mockJobsData,
            filters: baseFilters,
            data: jvmData,
            isPlaceholderData: false,
            allJobs: jvmData.items,
            setAllJobs: vi.fn(),
        });

        const { rerender } = renderHook(() => useViewer());
        expect(mockJobSelection.setSelectionMode).not.toHaveBeenCalledWith('all');

        mockJobSelection.setSelectionMode.mockClear();
        setJobsData({
            ...mockJobsData,
            filters: { ...baseFilters, auto_select_all: true },
            data: jvmData,
            isPlaceholderData: false,
            allJobs: jvmData.items,
            setAllJobs: vi.fn(),
        });
        rerender();

        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('all');
    });
});