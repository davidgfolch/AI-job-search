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

    it('regression: auto-select-all applies only when the Clean config real data loads and is not leaked on switch away', () => {
        const mockSetAllJobs = vi.fn();
        const cleanData = { items: [{ id: 1 }], page: 1, total: 1 };
        const jvmData = { items: [{ id: 200 }], page: 1, total: 1 };

        (useJobSelection as any).mockReturnValue({
            ...mockJobSelection,
            setSelectionMode: mockJobSelection.setSelectionMode,
        });
        mockJobSelection.setSelectionMode.mockClear();

        (useJobsData as any).mockReturnValue({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'jvm', page: 1 },
            data: jvmData,
            isPlaceholderData: false,
            allJobs: jvmData.items,
            setAllJobs: mockSetAllJobs,
        });

        const { rerender, result } = renderHook(() => useViewer());

        // Load the 'Clean - Ignore jobs by title' config and let its real data arrive
        act(() => { result.current.actions.setActiveConfigName('Clean - Ignore jobs by title'); });
        (useJobsData as any).mockReturnValue({
            ...mockJobsData,
            filters: { ...mockJobsData.filters, sql_filter: 'clean', page: 1 },
            data: cleanData,
            isPlaceholderData: false,
            allJobs: cleanData.items,
            setAllJobs: mockSetAllJobs,
        });
        rerender();

        expect(mockJobSelection.setSelectionMode).toHaveBeenCalledWith('all');

        mockJobSelection.setSelectionMode.mockClear();

        // Switch away to another config: its data must NOT auto-select all
        act(() => { result.current.actions.setActiveConfigName('JVM Spring'); });
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
});