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
        // Wait for FilterConfigurations async load to avoid act warnings
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });
        return result;
    };

    it('handles sort field changes', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const sortFieldSelect = screen.getByLabelText('Sort Field');
        fireEvent.change(sortFieldSelect, { target: { value: 'salary' } });
        // Default direction is desc (based on mockFilters or default fallback)
        // If mockFilters.order is undefined, it defaults to 'created desc' in UI logic? 
        // Actually UI uses: filters.order?.split(' ')[1] || 'desc'
        // So if we change field to salary, it should become 'salary desc'
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ order: 'salary desc' });
    });

    it('handles sort direction changes', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const sortDirSelect = screen.getByLabelText('Sort Direction');
        fireEvent.change(sortDirSelect, { target: { value: 'asc' } });
        // Default field is created
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ order: 'created asc' });
    });

    it('preserves direction when changing field', async () => {
        const filtersWithOrder: JobListParams = {
            ...mockFilters,
            order: 'salary asc',
        };
        await renderAndWait(<Filters filters={filtersWithOrder} onFiltersChange={onFiltersChangeMock} />);
        const sortFieldSelect = screen.getByLabelText('Sort Field');
        fireEvent.change(sortFieldSelect, { target: { value: 'modified' } });
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ order: 'modified asc' });
    });

    it('preserves field when changing direction', async () => {
        const filtersWithOrder: JobListParams = {
            ...mockFilters,
            order: 'salary desc',
        };
        await renderAndWait(<Filters filters={filtersWithOrder} onFiltersChange={onFiltersChangeMock} />);
        const sortDirSelect = screen.getByLabelText('Sort Direction');
        fireEvent.change(sortDirSelect, { target: { value: 'asc' } });
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ order: 'salary asc' });
    });
});
