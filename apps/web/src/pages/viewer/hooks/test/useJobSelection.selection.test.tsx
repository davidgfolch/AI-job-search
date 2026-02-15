import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobSelection } from '../useJobSelection';
import { MemoryRouter } from 'react-router-dom';

describe('useJobSelection - selection', () => {
    const defaultProps = {
        allJobs: [] as any[],
        filters: { page: 1 },
        setFilters: vi.fn(),
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    const createWrapper = (search = '') => {
        return ({ children }: { children: React.ReactNode }) => (
            <MemoryRouter initialEntries={[search ? `/?${search}` : '/']}>
                {children}
            </MemoryRouter>
        );
    };

    it('initializes with empty selection', () => {
        const { result } = renderHook(() => useJobSelection(defaultProps), { 
            wrapper: createWrapper() 
        });
        
        expect(result.current.selectedJob).toBeNull();
        expect(result.current.selectedIds.size).toBe(0);
        expect(result.current.selectionMode).toBe('none');
    });

    it('selects a job and updates selection state', () => {
        const jobs = [{ id: 1, title: 'Job A' }, { id: 2, title: 'Job B' }] as any[];
        const props = { ...defaultProps, allJobs: jobs };
        
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.handleJobSelect(jobs[0]);
        });

        expect(result.current.selectedJob).toEqual(jobs[0]);
        expect(result.current.selectedIds).toEqual(new Set([1]));
        expect(result.current.selectionMode).toBe('manual');
    });

    it('selects job via handleJobSelect and syncs selectedIds (checkbox state)', () => {
        const jobs = [
            { id: 1, title: 'Job A' },
            { id: 2, title: 'Job B' },
            { id: 3, title: 'Job C' }
        ] as any[];
        const props = { ...defaultProps, allJobs: jobs };
        
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.handleJobSelect(jobs[1]);
        });

        expect(result.current.selectedJob).toEqual(jobs[1]);
        expect(result.current.selectedIds).toEqual(new Set([2]));
    });

    it('selects job via URL jobId parameter and syncs selectedIds', async () => {
        const jobs = [{ id: 5, title: 'Job A' }] as any[];
        const props = { ...defaultProps, allJobs: jobs };
        
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper('jobId=5') 
        });

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 100));
        });

        expect(result.current.selectedJob).toEqual(jobs[0]);
        expect(result.current.selectedIds).toEqual(new Set([5]));
    });

    it('sets selection mode', () => {
        const { result } = renderHook(() => useJobSelection(defaultProps), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.setSelectionMode('all');
        });

        expect(result.current.selectionMode).toBe('all');
    });

    it('sets selected IDs directly', () => {
        const { result } = renderHook(() => useJobSelection(defaultProps), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.setSelectedIds(new Set([1, 2, 3]));
        });

        expect(result.current.selectedIds).toEqual(new Set([1, 2, 3]));
    });

    it('sets selected job directly', () => {
        const job = { id: 1, title: 'Test Job' } as any;
        const { result } = renderHook(() => useJobSelection(defaultProps), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.setSelectedJob(job);
        });

        expect(result.current.selectedJob).toEqual(job);
    });
});
