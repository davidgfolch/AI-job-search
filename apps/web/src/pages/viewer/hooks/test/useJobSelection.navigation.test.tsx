import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobSelection } from '../useJobSelection';
import { MemoryRouter } from 'react-router-dom';

describe('useJobSelection - navigation', () => {
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

    it('navigates to next job', () => {
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
            result.current.handleJobSelect(jobs[0]);
        });

        act(() => {
            result.current.navigateJob('next');
        });

        expect(result.current.selectedJob).toEqual(jobs[1]);
    });

    it('navigates to previous job', () => {
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

        act(() => {
            result.current.navigateJob('previous');
        });

        expect(result.current.selectedJob).toEqual(jobs[0]);
    });

    it('does not navigate past the end of the list', () => {
        const jobs = [{ id: 1, title: 'Job A' }] as any[];
        const props = { ...defaultProps, allJobs: jobs };
        
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.handleJobSelect(jobs[0]);
        });

        act(() => {
            result.current.navigateJob('next');
        });

        expect(result.current.selectedJob).toEqual(jobs[0]);
    });

    it('does not navigate before the start of the list', () => {
        const jobs = [{ id: 1, title: 'Job A' }] as any[];
        const props = { ...defaultProps, allJobs: jobs };
        
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.handleJobSelect(jobs[0]);
        });

        act(() => {
            result.current.navigateJob('previous');
        });

        expect(result.current.selectedJob).toEqual(jobs[0]);
    });

    it('loads more when navigating past last job with more pages', () => {
        const jobs = [{ id: 1, title: 'Job A' }] as any[];
        const onLoadMore = vi.fn();
        const props = { ...defaultProps, allJobs: jobs, hasMorePages: true, onLoadMore };
        
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.handleJobSelect(jobs[0]);
        });

        act(() => {
            result.current.navigateJob('next');
        });

        expect(onLoadMore).toHaveBeenCalled();
    });

    it('handles empty job list for navigation', () => {
        const props = { ...defaultProps, allJobs: [] };
        const { result } = renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper() 
        });

        act(() => {
            result.current.navigateJob('next');
        });

        expect(result.current.selectedJob).toBeNull();
    });
});
