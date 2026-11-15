import { renderHook } from '@testing-library/react';
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

describe('useViewer regression', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useJobsData as any).mockReturnValue(mockJobsData);
        (useJobSelection as any).mockReturnValue(mockJobSelection);
        (useJobMutations as any).mockReturnValue(mockJobMutations);
        (useModalityValues as any).mockReturnValue({ data: [] });
    });

    it('regression: list is replaced with the new config jobs after a config switch (placeholder data ignored)', () => {
        const mockSetAllJobs = vi.fn();
        const cleanData = { items: [{ id: 1 }], page: 1, total: 1 };
        const jvmData = { items: [{ id: 200 }], page: 1, total: 1 };

        (useJobsData as any).mockReturnValue({
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
        (useJobsData as any).mockReturnValue({
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
        (useJobsData as any).mockReturnValue({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'jvm', page: 1 },
            data: jvmData,
            isPlaceholderData: false,
            allJobs: [],
            setAllJobs: mockSetAllJobs,
        });
        rerender();

        const updater = mockSetAllJobs.mock.calls.map(call => call[0]).find(arg => typeof arg === 'function');
        expect(updater).toBeDefined();
        expect((updater as any)([])).toEqual(jvmData.items);
    });

    it('regression: auto-select-all is driven by filters.auto_select_all and not by the config name', () => {
        const mockSetAllJobs = vi.fn();
        const cleanData = { items: [{ id: 1 }], page: 1, total: 1 };
        const jvmData = { items: [{ id: 200 }], page: 1, total: 1 };

        // A configuration with auto_select_all selects every matching job as soon as its page-1 data is shown.
        (useJobsData as any).mockReturnValue({
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
        (useJobSelection as any).mockReturnValue({ ...mockJobSelection, selectionMode: 'none' });
        rerender();
        expect(mockJobSelection.setSelectionMode).not.toHaveBeenCalledWith('all');

        // Switching to a configuration without the flag never selects all.
        (useJobSelection as any).mockReturnValue({ ...mockJobSelection, selectionMode: 'manual' });
        (useJobsData as any).mockReturnValue({
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

        (useJobsData as any).mockReturnValue({
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
        (useJobsData as any).mockReturnValue({
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