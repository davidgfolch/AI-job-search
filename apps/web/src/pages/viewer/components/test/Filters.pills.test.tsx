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

describe('Filters - Pills', () => {
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
});
