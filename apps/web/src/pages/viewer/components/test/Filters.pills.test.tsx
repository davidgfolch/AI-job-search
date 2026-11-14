import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
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
        await waitFor(() => expect(screen.queryByRole('progressbar')).not.toBeInTheDocument());
        return result;
    };

    it('renders all boolean filter pills in Include section', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
        const includeSection = screen.getAllByText(/Include:/)[0].closest('.pills-section');
        expect(includeSection).toBeInTheDocument();
        expect(screen.getAllByText('Flagged').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Like').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Applied').length).toBeGreaterThan(0);
    });

    it('renders all boolean filter pills in Exclude section', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
        const excludeSection = screen.getAllByText(/Exclude:/)[0].closest('.pills-section');
        expect(excludeSection).toBeInTheDocument();
    });

    it('hides the interview pipeline pills from Include and Exclude sections', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
        const sections = screen.getAllByText(/Include:|Exclude:/)
            .map(label => label.closest('.pills-section') as HTMLElement);
        const hiddenLabels = ['Interview (RH)', 'Interview', 'Interview (Tech)', 'Technical Test', 'Technical Test Done'];
        sections.forEach(section => {
            hiddenLabels.forEach(label => expect(within(section).queryByText(label)).not.toBeInTheDocument());
        });
    });

    describe.each(['Flagged', 'Like', 'Applied'])('for %s pill', (pillName) => {
        const filterKey = pillName.toLowerCase() === 'Like' ? 'liked' : pillName.toLowerCase();
        
        it(`toggles ${pillName} include pill correctly`, async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            const pills = screen.getAllByText(pillName);
            const includePill = pills[0];
            fireEvent.click(includePill);
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ [filterKey]: true });
        });

        it(`toggles ${pillName} exclude pill correctly`, async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            const pills = screen.getAllByText(pillName);
            const excludePill = pills[1];
            fireEvent.click(excludePill);
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ [filterKey]: false });
        });

        it(`shows active state for ${pillName} include pill`, async () => {
            const filtersWithInclude: JobListParams = {
                ...mockFilters,
                [filterKey]: true,
            };
            await renderAndWait(<Filters filters={filtersWithInclude} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            const includePill = screen.getAllByText(pillName)[0];
            expect(includePill).toHaveClass('active-true');
        });

        it(`shows active state for ${pillName} exclude pill`, async () => {
            const filtersWithExclude: JobListParams = {
                ...mockFilters,
                [filterKey]: false,
            };
            await renderAndWait(<Filters filters={filtersWithExclude} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            const excludePill = screen.getAllByText(pillName)[1];
            expect(excludePill).toHaveClass('active-false');
        });

        it(`toggles off ${pillName} filter when clicking same pill again`, async () => {
            const filtersWithActive: JobListParams = {
                ...mockFilters,
                [filterKey]: true,
            };
            await renderAndWait(<Filters filters={filtersWithActive} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            const includePill = screen.getAllByText(pillName)[0];
            fireEvent.click(includePill);
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ [filterKey]: undefined });
        });
    });

    describe('Auto select all pill', () => {
        it('renders below the modality box, right of the include/exclude box', async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} modalityValues={['remote']} />);
            const pill = screen.getByText('Auto select all');
            const sideColumn = pill.closest('.filters-side-column');
            expect(sideColumn).toBeInTheDocument();
            expect(screen.getByText('Selection:')).toBeInTheDocument();
            const modalityGroup = sideColumn?.querySelector('.modality-filter-group');
            expect(modalityGroup).toBeInTheDocument();
            expect(modalityGroup!.compareDocumentPosition(pill) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
        });

        it('enables the flag when clicked', async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            fireEvent.click(screen.getByText('Auto select all'));
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ auto_select_all: true });
        });

        it('shows the active state when the flag is set', async () => {
            await renderAndWait(<Filters filters={{ ...mockFilters, auto_select_all: true }} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            expect(screen.getByText('Auto select all')).toHaveClass('active-true');
        });

        it('disables the flag when clicked again, persisting null as unselected', async () => {
            await renderAndWait(<Filters filters={{ ...mockFilters, auto_select_all: true }} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            fireEvent.click(screen.getByText('Auto select all'));
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ auto_select_all: null });
        });

        it('treats null as unselected', async () => {
            await renderAndWait(<Filters filters={{ ...mockFilters, auto_select_all: null }} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            expect(screen.getByText('Auto select all')).not.toHaveClass('active-true');
        });

        it('explains that it selects the whole filter, not only the loaded pages', async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} configCount={0} />);
            expect(screen.getByText('Auto select all')).toHaveAttribute(
                'title',
                'Auto select all jobs in the filter, including pages that are not loaded');
        });
    });
});