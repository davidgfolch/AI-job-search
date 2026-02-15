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
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });
        return result;
    };

    it('renders with default collapsed state', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        expect(screen.getByText(/Filters/)).toBeInTheDocument();
        // Should not be expanded by default (configCount undefined)
        expect(screen.queryByPlaceholderText('Search jobs...')).not.toBeInTheDocument();
    });

    it('expands when configCount is 0', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
        expect(screen.getByPlaceholderText('Search jobs...')).toBeInTheDocument();
    });

    it('collapses when configCount is greater than 0', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={5} />);
        expect(screen.queryByPlaceholderText('Search jobs...')).not.toBeInTheDocument();
    });

    it('renders FilterConfigurations component', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
    });

    it('expands and collapses when toggle button is clicked', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const toggleButton = screen.getByText(/Filters/);
        // Default is collapsed
        expect(screen.queryByPlaceholderText('Search jobs...')).not.toBeInTheDocument();
        
        // Click to expand
        fireEvent.click(toggleButton);
        expect(screen.getByPlaceholderText('Search jobs...')).toBeInTheDocument();
        
        // Click to collapse
        fireEvent.click(toggleButton);
        expect(screen.queryByPlaceholderText('Search jobs...')).not.toBeInTheDocument();
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

    describe.each([
        { 
            name: 'search input', 
            selector: 'Search jobs...', 
            value: 'React Developer', 
            expectedKey: 'search',
            expectedValue: 'React Developer',
            includePage: true
        },
        { 
            name: 'days old filter', 
            label: /Days old/, 
            value: '7', 
            expectedKey: 'days_old',
            expectedValue: 7
        },
        { 
            name: 'salary regex filter', 
            label: /Salary/, 
            value: '\\d{6}', 
            expectedKey: 'salary',
            expectedValue: '\\d{6}'
        },
        { 
            name: 'SQL where filter', 
            placeholder: /e.g. salary/, 
            value: 'salary > 50000', 
            expectedKey: 'sql_filter',
            expectedValue: 'salary > 50000'
        }
    ])('handles $name', ({ selector, label, placeholder, value, expectedKey, expectedValue, includePage }) => {
        it(`should update ${expectedKey} filter correctly`, async () => {
             // Pass configCount={0} to force expand so inputs are visible
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            
            const input = selector 
                ? screen.getByPlaceholderText(selector)
                : label 
                    ? screen.getByLabelText(label)
                    : screen.getByPlaceholderText(placeholder);
            
            fireEvent.change(input, { target: { value } });
            
            const expectedCall = includePage
                ? { ...mockFilters, [expectedKey]: expectedValue, page: 1 }
                : { [expectedKey]: expectedValue };
                
            expect(onFiltersChangeMock).toHaveBeenCalledWith(expectedCall);
        });
    });
});