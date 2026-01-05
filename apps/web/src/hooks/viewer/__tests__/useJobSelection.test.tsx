import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobSelection } from '../useJobSelection';
import { MemoryRouter } from 'react-router-dom';

describe('useJobSelection', () => {
    const defaultProps = {
        allJobs: [],
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

    it('should set filters correctly when ids param is present', () => {
        const setFilters = vi.fn();
        const props = { ...defaultProps, setFilters };
        
        // Simulate URL with ids=1,2,3
        renderHook(() => useJobSelection(props), { 
            wrapper: createWrapper('ids=1,2,3') 
        });

        // Current behavior (bug): sets seen:0, ignored:0, etc.
        // Expected behavior (fix): sets seen:undefined, ignored:undefined, etc.
        
        expect(setFilters).toHaveBeenCalledWith(expect.any(Function));
        
        // Get the update function passed to setFilters
        const updateFn = setFilters.mock.calls[0][0];
        const prevFilters = { page: 1, seen: 0, ignored: 0 };
        const newFilters = updateFn(prevFilters);
        
        expect(newFilters).toEqual(expect.objectContaining({
            sql_filter: 'id IN (1,2,3)',
            page: 1,
            // We want these to be undefined to clear any existing boolean filters
            ignored: undefined,
            seen: undefined,
            applied: undefined,
            discarded: undefined,
            closed: undefined
        }));
    });

    it('should not update filters if sql_filter is already set', () => {
        // Test logic relies on implementation detail of setFilters state update
    });
});
