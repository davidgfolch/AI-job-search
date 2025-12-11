import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Filters from '../Filters';
import type { JobListParams } from '../../api/jobs';
import { createMockFilters } from '../../__tests__/test-utils';

describe('Filters', () => {
    const mockFilters = createMockFilters();

    let onFiltersChangeMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onFiltersChangeMock = vi.fn();
    });

    it('renders with default collapsed state', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        expect(screen.getByText(/Filters/)).toBeInTheDocument();
    });

    it('renders FilterConfigurations component', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        expect(screen.getByLabelText(/Filter Configurations/i)).toBeInTheDocument();
    });

    it('expands and collapses when toggle button is clicked', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const toggleButton = screen.getByText(/Filters/);

        // Should be expanded by default
        expect(screen.getByPlaceholderText('Search jobs...')).toBeInTheDocument();

        // Click to collapse
        fireEvent.click(toggleButton);
        expect(screen.queryByPlaceholderText('Search jobs...')).not.toBeInTheDocument();

        // Click to expand again
        fireEvent.click(toggleButton);
        expect(screen.getByPlaceholderText('Search jobs...')).toBeInTheDocument();
    });

    it('shows active indicator when filters are set', () => {
        const filtersWithActive: JobListParams = {
            ...mockFilters,
            flagged: true,
        };

        render(<Filters filters={filtersWithActive} onFiltersChange={onFiltersChangeMock} />);

        const toggleButton = screen.getByText(/Filters/);
        expect(toggleButton).toHaveClass('has-active');
        expect(screen.getByText('●')).toBeInTheDocument();
    });

    it('handles search input changes', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const searchInput = screen.getByPlaceholderText('Search jobs...');
        fireEvent.change(searchInput, { target: { value: 'React Developer' } });

        expect(onFiltersChangeMock).toHaveBeenCalledWith({
            ...mockFilters,
            search: 'React Developer',
            page: 1,
        });
    });

    it('handles days old filter', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const daysOldInput = screen.getByLabelText(/Days old/);
        fireEvent.change(daysOldInput, { target: { value: '7' } });

        expect(onFiltersChangeMock).toHaveBeenCalledWith({ days_old: 7 });
    });

    it('handles salary regex filter', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const salaryInput = screen.getByLabelText(/Salary/);
        fireEvent.change(salaryInput, { target: { value: '\\d{6}' } });

        expect(onFiltersChangeMock).toHaveBeenCalledWith({ salary: '\\d{6}' });
    });

    it('handles SQL where filter', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const sqlInput = screen.getByPlaceholderText(/e.g. salary/);
        fireEvent.change(sqlInput, { target: { value: 'salary > 50000' } });

        expect(onFiltersChangeMock).toHaveBeenCalledWith({ sql_filter: 'salary > 50000' });
    });

    it('handles sort order changes', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const sortSelect = screen.getByLabelText(/Sort/);
        fireEvent.change(sortSelect, { target: { value: 'salary desc' } });

        expect(onFiltersChangeMock).toHaveBeenCalledWith({ order: 'salary desc' });
    });

    it('renders all boolean filter pills in Include section', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const includeSection = screen.getAllByText(/Include:/)[0].closest('.pills-section');
        expect(includeSection).toBeInTheDocument();

        // Check for some filter pills
        expect(screen.getAllByText('Flagged').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Like').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Applied').length).toBeGreaterThan(0);
    });

    it('renders all boolean filter pills in Exclude section', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const excludeSection = screen.getAllByText(/Exclude:/)[0].closest('.pills-section');
        expect(excludeSection).toBeInTheDocument();
    });

    it('toggles include filter pill correctly', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        // Find the first "Flagged" pill (in Include section)
        const flaggedPills = screen.getAllByText('Flagged');
        const includeFlaggedPill = flaggedPills[0];

        fireEvent.click(includeFlaggedPill);

        expect(onFiltersChangeMock).toHaveBeenCalledWith({ flagged: true });
    });

    it('toggles exclude filter pill correctly', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        // Find the second "Flagged" pill (in Exclude section)
        const flaggedPills = screen.getAllByText('Flagged');
        const excludeFlaggedPill = flaggedPills[1];

        fireEvent.click(excludeFlaggedPill);

        expect(onFiltersChangeMock).toHaveBeenCalledWith({ flagged: false });
    });

    it('shows active state for include pills', () => {
        const filtersWithInclude: JobListParams = {
            ...mockFilters,
            flagged: true,
        };

        render(<Filters filters={filtersWithInclude} onFiltersChange={onFiltersChangeMock} />);

        const includeFlaggedPill = screen.getAllByText('Flagged')[0];
        expect(includeFlaggedPill).toHaveClass('active-true');
    });

    it('shows active state for exclude pills', () => {
        const filtersWithExclude: JobListParams = {
            ...mockFilters,
            discarded: false,
        };

        render(<Filters filters={filtersWithExclude} onFiltersChange={onFiltersChangeMock} />);

        const excludeDiscardedPill = screen.getAllByText('Discarded')[1];
        expect(excludeDiscardedPill).toHaveClass('active-false');
    });

    it('toggles off filter when clicking same pill again', () => {
        const filtersWithFlagged: JobListParams = {
            ...mockFilters,
            flagged: true,
        };

        render(<Filters filters={filtersWithFlagged} onFiltersChange={onFiltersChangeMock} />);

        const includeFlaggedPill = screen.getAllByText('Flagged')[0];
        fireEvent.click(includeFlaggedPill);

        // Should toggle off (set to undefined)
        expect(onFiltersChangeMock).toHaveBeenCalledWith({ flagged: undefined });
    });

    it('displays all sort options', () => {
        render(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);

        const sortSelect = screen.getByLabelText(/Sort/);

        expect(sortSelect).toHaveTextContent('Created (Newest)');
        expect(sortSelect).toHaveTextContent('Created (Oldest)');
        expect(sortSelect).toHaveTextContent('Salary (High-Low)');
        expect(sortSelect).toHaveTextContent('Salary (Low-High)');
        expect(sortSelect).toHaveTextContent('Match % (High-Low)');
    });
});
