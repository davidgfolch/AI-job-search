import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Filters from '../Filters';
import type { JobListParams } from '../../../api/ViewerApi';
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

    let onFiltersChangeMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onFiltersChangeMock = vi.fn();
    });

    const renderAndWait = async (ui: React.ReactElement) => {
        const result = render(ui);
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


    it('renders all boolean filter pills in Include section', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const includeSection = screen.getAllByText(/Include:/)[0].closest('.pills-section');
        expect(includeSection).toBeInTheDocument();
        // Check for some filter pills
        expect(screen.getAllByText('Flagged').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Like').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Applied').length).toBeGreaterThan(0);
    });

    it('renders all boolean filter pills in Exclude section', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const excludeSection = screen.getAllByText(/Exclude:/)[0].closest('.pills-section');
        expect(excludeSection).toBeInTheDocument();
    });

    it('toggles include filter pill correctly', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        // Find the first "Flagged" pill (in Include section)
        const flaggedPills = screen.getAllByText('Flagged');
        const includeFlaggedPill = flaggedPills[0];
        fireEvent.click(includeFlaggedPill);
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ flagged: true });
    });

    it('toggles exclude filter pill correctly', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        // Find the second "Flagged" pill (in Exclude section)
        const flaggedPills = screen.getAllByText('Flagged');
        const excludeFlaggedPill = flaggedPills[1];
        fireEvent.click(excludeFlaggedPill);
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ flagged: false });
    });

    it('shows active state for include pills', async () => {
        const filtersWithInclude: JobListParams = {
            ...mockFilters,
            flagged: true,
        };
        await renderAndWait(<Filters filters={filtersWithInclude} onFiltersChange={onFiltersChangeMock} />);
        const includeFlaggedPill = screen.getAllByText('Flagged')[0];
        expect(includeFlaggedPill).toHaveClass('active-true');
    });

    it('shows active state for exclude pills', async () => {
        const filtersWithExclude: JobListParams = {
            ...mockFilters,
            discarded: false,
        };
        await renderAndWait(<Filters filters={filtersWithExclude} onFiltersChange={onFiltersChangeMock} />);
        const excludeDiscardedPill = screen.getAllByText('Discarded')[1];
        expect(excludeDiscardedPill).toHaveClass('active-false');
    });

    it('toggles off filter when clicking same pill again', async () => {
        const filtersWithFlagged: JobListParams = {
            ...mockFilters,
            flagged: true,
        };
        await renderAndWait(<Filters filters={filtersWithFlagged} onFiltersChange={onFiltersChangeMock} />);
        const includeFlaggedPill = screen.getAllByText('Flagged')[0];
        fireEvent.click(includeFlaggedPill);
        // Should toggle off (set to undefined)
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ flagged: undefined });
    });

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
