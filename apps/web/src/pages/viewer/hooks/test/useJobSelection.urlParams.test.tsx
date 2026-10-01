import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { useJobSelection } from '../useJobSelection';

const jobs = [{ id: 1, title: 'Job A' }, { id: 2, title: 'Job B' }, { id: 3, title: 'Job C' }] as any[];

const createWrapper = (search = '') => {
    return ({ children }: { children: React.ReactNode }) => (
        <MemoryRouter initialEntries={[search ? `/?${search}` : '/']}>
            {children}
        </MemoryRouter>
    );
};

type Props = Parameters<typeof useJobSelection>[0];

const renderWithUrl = (search: string, overrides: Partial<Props> = {}) => {
    const setFilters = vi.fn();
    const view = renderHook((props: Props) => useJobSelection(props), {
        wrapper: createWrapper(search),
        initialProps: { allJobs: jobs, filters: { page: 1, size: 20 }, setFilters, ...overrides } as Props,
    });
    return { ...view, setFilters, baseFilters: (overrides.filters ?? { page: 1, size: 20 }) as any };
};

/** setFilters is always called with an updater, so the caller supplies the previous state. */
const resolveFilters = (setFilters: ReturnType<typeof vi.fn>, prev: any) => {
    const arg = setFilters.mock.calls.at(-1)![0];
    return typeof arg === 'function' ? arg(prev) : arg;
};

describe('useJobSelection - URL parameters', () => {
    beforeEach(() => vi.clearAllMocks());

    describe('jobId parameter', () => {
        it('restricts the list to the job in the URL', () => {
            const { setFilters } = renderWithUrl('jobId=2');
            expect(resolveFilters(setFilters, { page: 1, size: 20 })).toEqual({ page: 1, size: 20, sql_filter: 'id=2' });
        });

        it('keeps the previous filters when the URL already matches', () => {
            const prev = { page: 1, size: 20, sql_filter: 'id=2' };
            const { setFilters } = renderWithUrl('jobId=2', { filters: prev as any });
            expect(resolveFilters(setFilters, prev)).toBe(prev);
        });

        it('selects the job from the URL and syncs the checkbox state', () => {
            const { result } = renderWithUrl('jobId=3');
            expect(result.current.selectedJob?.id).toBe(3);
            expect([...result.current.selectedIds]).toEqual([3]);
        });

        it('selects nothing when the URL job is not in the list', () => {
            const { result } = renderWithUrl('jobId=99');
            expect(result.current.selectedJob).toBeNull();
        });

        it('ignores a malformed jobId', () => {
            const { setFilters } = renderWithUrl('jobId=abc');
            expect(setFilters).not.toHaveBeenCalled();
        });

        it('does nothing without a jobId parameter', () => {
            const { result, setFilters } = renderWithUrl('page=2');
            expect(setFilters).not.toHaveBeenCalled();
            expect(result.current.selectedJob).toBeNull();
        });
    });

    describe('ids parameter', () => {
        it('builds an IN filter and clears the per-state flags', () => {
            const prev = { page: 4, size: 20, ignored: true, seen: true };
            const { setFilters } = renderWithUrl('ids=1,3', { filters: prev as any });
            expect(resolveFilters(setFilters, prev)).toMatchObject({ sql_filter: 'id IN (1,3)', page: 1, ignored: undefined, seen: undefined });
        });

        it('keeps the filter when it is already applied', () => {
            const prev = { page: 1, size: 20, sql_filter: 'id IN (1,3)' };
            const { setFilters } = renderWithUrl('ids=1,3', { filters: prev as any });
            expect(resolveFilters(setFilters, prev)).toBe(prev);
        });

        it('drops entries that are not numbers', () => {
            const { setFilters } = renderWithUrl('ids=1,x,2');
            expect(resolveFilters(setFilters, { page: 1, size: 20 }).sql_filter).toBe('id IN (1,2)');
        });

        it('ignores an ids parameter with no valid ids', () => {
            const { setFilters } = renderWithUrl('ids=x');
            expect(setFilters).not.toHaveBeenCalled();
        });
    });

    describe('auto-selection after a data refetch', () => {
        const renderWithFlag = () => {
            const setFilters = vi.fn();
            const view = renderHook((props: Props) => useJobSelection(props), {
                wrapper: createWrapper(),
                initialProps: { allJobs: jobs, filters: { page: 1, size: 20 }, setFilters } as Props,
            });
            const flag = (previousJobId: number, previousJobIndex: number) =>
                act(() => {
                    view.result.current.autoSelectNext.current = { shouldSelect: true, previousJobId, previousJobIndex };
                });
            return { ...view, setFilters, flag };
        };

        it('selects the job that took the place of the filtered-out one', () => {
            const { result, rerender, flag } = renderWithFlag();
            flag(2, 1);
            const refreshed = [{ id: 1, title: 'Job A' }, { id: 3, title: 'Job C' }] as any[];
            rerender({ allJobs: refreshed, filters: { page: 1, size: 20 } } as Props);
            expect(result.current.selectedJob?.id).toBe(1);
            expect([...result.current.selectedIds]).toEqual([1]);
        });

        it('consumes the flag without touching the selection when the previous job survived', () => {
            const { result, rerender, flag } = renderWithFlag();
            flag(1, 0);
            rerender({ allJobs: [...jobs], filters: { page: 1, size: 20 } } as Props);
            expect(result.current.autoSelectNext.current.shouldSelect).toBe(false);
            expect(result.current.selectedJob).toBeNull();
        });

        it('clears the selection when no jobs are left', () => {
            const { result, rerender, flag } = renderWithFlag();
            flag(2, 1);
            rerender({ allJobs: [], filters: { page: 1, size: 20 } } as Props);
            expect(result.current.selectedJob).toBeNull();
            expect(result.current.selectedIds.size).toBe(0);
        });

        it('does nothing while the auto-selection flag is not set', () => {
            const { result, rerender } = renderWithFlag();
            rerender({ allJobs: [{ id: 9, title: 'New' }] as any[], filters: { page: 1, size: 20 } } as Props);
            expect(result.current.selectedJob).toBeNull();
        });
    });

    describe('filter changes', () => {
        it('resets the selection when a filter changes', () => {
            const setFilters = vi.fn();
            const { result, rerender } = renderHook((props: Props) => useJobSelection(props), {
                wrapper: createWrapper(),
                initialProps: { allJobs: jobs, filters: { page: 1, size: 20 }, setFilters } as Props,
            });

            act(() => {
                result.current.setSelectionMode('manual');
                result.current.setSelectedIds(new Set([1]));
            });
            expect(result.current.selectionMode).toBe('manual');

            rerender({ allJobs: jobs, filters: { page: 1, size: 20, search: 'python' } } as Props);

            expect(result.current.selectionMode).toBe('none');
            expect(result.current.selectedIds.size).toBe(0);
        });

        it('keeps the selection when only the page changes', () => {
            const setFilters = vi.fn();
            const { result, rerender } = renderHook((props: Props) => useJobSelection(props), {
                wrapper: createWrapper(),
                initialProps: { allJobs: jobs, filters: { page: 1, size: 20 }, setFilters } as Props,
            });

            act(() => {
                result.current.setSelectionMode('manual');
                result.current.setSelectedIds(new Set([1]));
            });
            rerender({ allJobs: jobs, filters: { page: 2, size: 20 } } as Props);

            expect(result.current.selectionMode).toBe('manual');
            expect([...result.current.selectedIds]).toEqual([1]);
        });
    });
});