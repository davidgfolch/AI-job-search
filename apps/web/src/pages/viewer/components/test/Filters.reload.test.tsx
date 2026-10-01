import { render, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { JobListParams } from '../../api/ViewerApi';

// The decision lives in the onLoadConfig bridge Filters hands to FilterConfigurations, so the child is replaced
// by a stub that only records the callback. Everything else renders as usual.
let capturedOnLoadConfig: ((filters: JobListParams, name: string) => void) | undefined;
vi.mock('../FilterConfigurations', () => ({
    default: (props: { onLoadConfig: (filters: JobListParams, name: string) => void }) => {
        capturedOnLoadConfig = props.onLoadConfig;
        return null;
    }
}));

import Filters from '../Filters';
import { createMockFilters } from '../../test/test-utils';

describe('Filters - reloading the active configuration', () => {
    let onFiltersChange: ReturnType<typeof vi.fn>;
    let onReloadConfig: ReturnType<typeof vi.fn>;
    let onConfigNameChange: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        capturedOnLoadConfig = undefined;
        onFiltersChange = vi.fn();
        onReloadConfig = vi.fn();
        onConfigNameChange = vi.fn();
    });

    const renderFilters = (filters: JobListParams, props: Record<string, unknown> = {}) => {
        const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
        render(
            <QueryClientProvider client={queryClient}>
                <Filters filters={filters} onFiltersChange={onFiltersChange} onReloadConfig={onReloadConfig} onConfigNameChange={onConfigNameChange} configCount={0} {...props} />
            </QueryClientProvider>
        );
    };

    const loadConfig = (loaded: JobListParams, name = 'Backend') => {
        expect(capturedOnLoadConfig).toBeDefined();
        act(() => { capturedOnLoadConfig!(loaded, name); });
    };

    it('reloads the list when the configuration already in effect is applied again', () => {
        const filters = createMockFilters({ search: 'Backend', ai_enriched: true });
        renderFilters(filters);

        loadConfig({ search: 'Backend', ai_enriched: true, page: 1 });

        expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ search: 'Backend', page: 1 }));
        expect(onReloadConfig).toHaveBeenCalledTimes(1);
        expect(onConfigNameChange).toHaveBeenCalledWith('Backend');
    });

    it('reloads when a partial configuration merges into the filters already in effect', () => {
        const filters = createMockFilters({ search: 'Backend', ai_enriched: true, size: 20 });
        renderFilters(filters);

        // A configuration saved with only the filters the user changed: it inherits the rest from the current ones.
        loadConfig({ search: 'Backend', page: 1, size: 20 });

        expect(onReloadConfig).toHaveBeenCalledTimes(1);
    });

    it('does not reload when a different configuration is applied', () => {
        const filters = createMockFilters({ search: 'Backend', ai_enriched: true });
        renderFilters(filters);

        loadConfig({ search: 'Python', ai_enriched: true, page: 1 });

        expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ search: 'Python' }));
        expect(onReloadConfig).not.toHaveBeenCalled();
    });

    it('does not reload when the page is not the first one, since the query key already changes', () => {
        const filters = createMockFilters({ search: 'Backend', ai_enriched: true, page: 3 });
        renderFilters(filters);

        loadConfig({ search: 'Backend', ai_enriched: true, page: 1 });

        expect(onFiltersChange).toHaveBeenCalledWith(expect.objectContaining({ page: 1 }));
        expect(onReloadConfig).not.toHaveBeenCalled();
    });

    it('treats a filter cleared by the configuration as a change', () => {
        const filters = createMockFilters({ search: 'Backend', ai_enriched: true });
        renderFilters(filters);

        loadConfig({ search: 'Backend', ai_enriched: false, page: 1 });

        expect(onReloadConfig).not.toHaveBeenCalled();
    });

    it('loads without a reload handler', () => {
        const filters = createMockFilters({ search: 'Backend', ai_enriched: true });
        renderFilters(filters, { onReloadConfig: undefined });

        expect(() => loadConfig({ search: 'Backend', ai_enriched: true, page: 1 })).not.toThrow();
        expect(onFiltersChange).toHaveBeenCalledTimes(1);
    });
});
