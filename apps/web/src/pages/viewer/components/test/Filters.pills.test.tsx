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
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });
        return result;
    };

    it('renders all boolean filter pills in Include section', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const includeSection = screen.getAllByText(/Include:/)[0].closest('.pills-section');
        expect(includeSection).toBeInTheDocument();
        expect(screen.getAllByText('Flagged').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Like').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Applied').length).toBeGreaterThan(0);
    });

    it('renders all boolean filter pills in Exclude section', async () => {
        await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
        const excludeSection = screen.getAllByText(/Exclude:/)[0].closest('.pills-section');
        expect(excludeSection).toBeInTheDocument();
    });

    describe.each(['Flagged', 'Like', 'Applied'])('for %s pill', (pillName) => {
        const filterKey = pillName.toLowerCase() === 'Like' ? 'liked' : pillName.toLowerCase();
        
        it(`toggles ${pillName} include pill correctly`, async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
            const pills = screen.getAllByText(pillName);
            const includePill = pills[0];
            fireEvent.click(includePill);
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ [filterKey]: true });
        });

        it(`toggles ${pillName} exclude pill correctly`, async () => {
            await renderAndWait(<Filters filters={mockFilters} onFiltersChange={onFiltersChangeMock} />);
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
            await renderAndWait(<Filters filters={filtersWithInclude} onFiltersChange={onFiltersChangeMock} />);
            const includePill = screen.getAllByText(pillName)[0];
            expect(includePill).toHaveClass('active-true');
        });

        it(`shows active state for ${pillName} exclude pill`, async () => {
            const filtersWithExclude: JobListParams = {
                ...mockFilters,
                [filterKey]: false,
            };
            await renderAndWait(<Filters filters={filtersWithExclude} onFiltersChange={onFiltersChangeMock} />);
            const excludePill = screen.getAllByText(pillName)[1];
            expect(excludePill).toHaveClass('active-false');
        });

        it(`toggles off ${pillName} filter when clicking same pill again`, async () => {
            const filtersWithActive: JobListParams = {
                ...mockFilters,
                [filterKey]: true,
            };
            await renderAndWait(<Filters filters={filtersWithActive} onFiltersChange={onFiltersChangeMock} />);
            const includePill = screen.getAllByText(pillName)[0];
            fireEvent.click(includePill);
            expect(onFiltersChangeMock).toHaveBeenCalledWith({ [filterKey]: undefined });
        });
    });
});