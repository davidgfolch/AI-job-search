import { render, screen, fireEvent, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Filters from '../Filters';
import type { JobListParams } from '../../api/ViewerApi';
import { createMockFilters } from '../../test/test-utils';

vi.mock('../../hooks/FilterConfigService', () => {
    return {
        FilterConfigService: class {
            load = vi.fn().mockResolvedValue([]);
            save = vi.fn().mockResolvedValue(undefined);
        }
    }
});

describe('Filters - Sort', () => {
    const mockFilters = createMockFilters();

    let onFiltersChangeMock: (filters: Partial<JobListParams>) => void;

    beforeEach(() => {
        onFiltersChangeMock = vi.fn();
    });

    const renderAndWait = async (ui: React.ReactElement) => {
        const queryClient = new QueryClient({
            defaultOptions: { queries: { retry: false } },
        });

        const result = render(
            <QueryClientProvider client={queryClient}>
                {ui}
            </QueryClientProvider>
        );
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });
        return result;
    };

    describe.each([
        { 
            field: 'salary', 
            direction: 'desc', 
            initialOrder: undefined, 
            changeType: 'field',
            expected: 'salary desc' 
        },
        { 
            field: 'modified', 
            direction: 'asc', 
            initialOrder: 'salary asc', 
            changeType: 'field',
            expected: 'modified asc' 
        },
        { 
            field: 'created', 
            direction: 'asc', 
            initialOrder: undefined, 
            changeType: 'direction',
            expected: 'created asc' 
        },
        { 
            field: 'salary', 
            direction: 'asc', 
            initialOrder: 'salary desc', 
            changeType: 'direction',
            expected: 'salary asc' 
        }
    ])('sort functionality', ({ field, direction, initialOrder, changeType, expected }) => {
        it(`should handle ${changeType} change to ${expected}`, async () => {
            const filters = initialOrder 
                ? { ...mockFilters, order: initialOrder }
                : mockFilters;
                
            await renderAndWait(<Filters filters={filters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            
            if (changeType === 'field') {
                const sortFieldSelect = screen.getByLabelText('Sort Field');
                fireEvent.change(sortFieldSelect, { target: { value: field } });
            } else {
                const sortDirSelect = screen.getByLabelText('Sort Direction');
                fireEvent.change(sortDirSelect, { target: { value: direction } });
            }
            
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ order: expected });
        });
    });
});