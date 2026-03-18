import React from 'react';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';

export const renderWithQueryClient = (ui: React.ReactElement) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });
    return render(
        <QueryClientProvider client={queryClient}>
            {ui}
        </QueryClientProvider>
    );
};

export const defaultProps = {
    chartType: 'weekday' as const,
    parentTimeRange: 'Last 3 months',
    parentIncludeOldJobs: true,
    onExpandChange: vi.fn(),
    onFilterChange: vi.fn(),
    expandedChart: null as string | null,
};
