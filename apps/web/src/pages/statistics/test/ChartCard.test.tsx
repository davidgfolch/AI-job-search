import { screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import './ChartCard.mocks'; // Important to load mocks first
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ChartCard from '../components/ChartCard';
import '@testing-library/jest-dom';
import { renderWithQueryClient, defaultProps } from './ChartCard.fixtures';

describe('ChartCard', () => {

    it.each([
        { 
            title: 'Test Chart', 
            children: <div data-testid="chart-content">Chart Content</div>, 
            expectedTitle: 'Test Chart', 
            expectedTestIds: ['chart-content'] 
        },
        { 
            title: 'Salary Distribution', 
            children: <div><div data-testid="chart-canvas">Canvas</div><div data-testid="chart-legend">Legend</div></div>, 
            expectedTitle: 'Salary Distribution', 
            expectedTestIds: ['chart-canvas', 'chart-legend'] 
        },
        { 
            title: 'Jobs in 2024 (Q1-Q2)', 
            children: <div>Content</div>, 
            expectedTitle: 'Jobs in 2024 (Q1-Q2)', 
            expectedTestIds: [] 
        }
    ])('renders correctly with title "$title"', ({ title, children, expectedTitle, expectedTestIds }) => {
        renderWithQueryClient(
            <ChartCard title={title} {...defaultProps}>
                {children}
            </ChartCard>
        );

        expect(screen.getByText(expectedTitle)).toBeInTheDocument();
        expectedTestIds.forEach(id => {
            expect(screen.getByTestId(id)).toBeInTheDocument();
        });
    });

    it('calls onExpandChange with title when expand button is clicked', () => {
        const handleExpandChange = vi.fn();
        renderWithQueryClient(
            <ChartCard title="Test Chart" {...defaultProps} onExpandChange={handleExpandChange}>
                <div>Chart Content</div>
            </ChartCard>
        );

        const expandButton = screen.getByTitle('Expand to Full Screen');
        fireEvent.click(expandButton);

        expect(handleExpandChange).toHaveBeenCalledWith('Test Chart');
    });

    it('renders expanded state when expandedChart matches title', () => {
        const { container } = renderWithQueryClient(
            <ChartCard title="Test Chart" {...defaultProps} expandedChart="Test Chart">
                <div>Chart Content</div>
            </ChartCard>
        );

        const section = container.querySelector('section');
        expect(section).toHaveClass('expanded');
        expect(screen.getByTitle('Close Full Screen')).toBeInTheDocument();
    });

    it('shows filter controls when expanded', () => {
        renderWithQueryClient(
            <ChartCard title="Test Chart" {...defaultProps} expandedChart="Test Chart">
                <div>Chart Content</div>
            </ChartCard>
        );

        expect(screen.getByText('Date Range:')).toBeInTheDocument();
        expect(screen.getByText('Include old jobs')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Last 3 months')).toBeInTheDocument();
    });

    it('calls onFilterChange and onExpandChange when closing full screen', () => {
        const handleExpandChange = vi.fn();
        const handleFilterChange = vi.fn();

        renderWithQueryClient(
            <ChartCard
                title="Test Chart"
                {...defaultProps}
                expandedChart="Test Chart"
                onExpandChange={handleExpandChange}
                onFilterChange={handleFilterChange}
            >
                <div>Chart Content</div>
            </ChartCard>
        );

        const closeButton = screen.getByTitle('Close Full Screen');
        fireEvent.click(closeButton);

        expect(handleFilterChange).toHaveBeenCalledWith('Last 3 months', true);
        expect(handleExpandChange).toHaveBeenCalledWith(null);
    });



    describe('edge cases', () => {
        it.each([
            {
                name: 'empty title',
                title: '',
                children: <div>Content</div>
            },
            {
                name: 'very long title',
                title: 'This is a very long chart title that might wrap or get truncated',
                children: <div>Content</div>
            },
            {
                name: 'empty children',
                title: 'Empty Chart',
                children: null
            }
        ])('handles $name', ({ title, children }) => {
            expect(() => renderWithQueryClient(
                <ChartCard title={title} {...defaultProps}>
                    {children}
                </ChartCard>
            )).not.toThrow();
        });
    });



    it('synchronizes local state with parent props when not expanded', () => {
        const { rerender } = renderWithQueryClient(
            <ChartCard
                title="Test Chart"
                {...defaultProps}
                parentTimeRange="Last month"
                parentIncludeOldJobs={false}
            >
                <div>Chart Content</div>
            </ChartCard>
        );

        // Expand the chart
        const expandButton = screen.getByTitle('Expand to Full Screen');
        fireEvent.click(expandButton);

        rerender(
            <QueryClientProvider client={new QueryClient()}>
                <ChartCard
                    title="Test Chart"
                    {...defaultProps}
                    parentTimeRange="Last month"
                    parentIncludeOldJobs={false}
                    expandedChart="Test Chart"
                >
                    <div>Chart Content</div>
                </ChartCard>
            </QueryClientProvider>
        );

        expect(screen.getByDisplayValue('Last month')).toBeInTheDocument();
        expect(screen.getByRole('checkbox')).not.toBeChecked();
    });


});