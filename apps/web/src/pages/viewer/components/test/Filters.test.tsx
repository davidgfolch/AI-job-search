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

describe('Filters', () => {
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

    it('renders with default collapsed state', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        expect(screen.getByText(/Filters/)).toBeInTheDocument();
    });

    it('renders FilterConfigurations component', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
    });

    it('expands and collapses when toggle button is clicked', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const toggleButton = screen.getByText(/Filters/);
        expect(screen.getByPlaceholderText('Search jobs...')).toBeInTheDocument(); // Should be expanded by default
        fireEvent.click(toggleButton); // Click to collapse
        expect(screen.queryByPlaceholderText('Search jobs...')).not.toBeInTheDocument();
        fireEvent.click(toggleButton); // Click to expand again
        expect(screen.getByPlaceholderText('Search jobs...')).toBeInTheDocument();
    });

    it('shows active indicator when filters are set', async () => {
        const filtersWithActive: JobListParams = {
            ...mockFilters,
            flagged: true,
        };
        await renderAndWait(<Filters filters={filtersWithActive} onFiltersChange={onFiltersChangeMock} />);
        const toggleButton = screen.getByText(/Filters/);
        expect(toggleButton).toHaveClass('has-active');
        expect(screen.getByText('●')).toBeInTheDocument();
    });

    it('handles search input changes', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const searchInput = screen.getByPlaceholderText('Search jobs...');
        fireEvent.change(searchInput, { target: { value: 'React Developer' } });
        expect(onFiltersChangeMock).toHaveBeenCalledWith({
            ...mockFilters,
            search: 'React Developer',
            page: 1,
        });
    });

    it('handles days old filter', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const daysOldInput = screen.getByLabelText(/Days old/);
        fireEvent.change(daysOldInput, { target: { value: '7' } });
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ days_old: 7 });
    });

    it('handles salary regex filter', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const salaryInput = screen.getByLabelText(/Salary/);
        fireEvent.change(salaryInput, { target: { value: '\\d{6}' } });
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ salary: '\\d{6}' });
    });

    it('handles SQL where filter', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const sqlInput = screen.getByPlaceholderText(/e.g. salary/);
        fireEvent.change(sqlInput, { target: { value: 'salary > 50000' } });
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ sql_filter: 'salary > 50000' });
    });



});
