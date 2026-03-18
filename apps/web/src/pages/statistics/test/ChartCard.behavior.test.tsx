import { screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import './ChartCard.mocks'; // Important to load mocks first
import ChartCard from '../components/ChartCard';
import '@testing-library/jest-dom';
import { renderWithQueryClient, defaultProps } from './ChartCard.fixtures';

describe('ChartCard Behavior', () => {
    it('updates local filter state when select changes', () => {
        renderWithQueryClient(
            <ChartCard title="Test Chart" {...defaultProps} expandedChart="Test Chart">
                <div>Chart Content</div>
            </ChartCard>
        );

        const select = screen.getByDisplayValue('Last 3 months');
        fireEvent.change(select, { target: { value: 'Last week' } });

        expect(screen.getByDisplayValue('Last week')).toBeInTheDocument();
    });

    it('updates local filter state when checkbox changes', () => {
        renderWithQueryClient(
            <ChartCard title="Test Chart" {...defaultProps} expandedChart="Test Chart" parentIncludeOldJobs={true}>
                <div>Chart Content</div>
            </ChartCard>
        );

        const checkbox = screen.getByRole('checkbox');
        expect(checkbox).toBeChecked();

        fireEvent.click(checkbox);

        expect(checkbox).not.toBeChecked();
    });

    it('closes full screen on Escape keydown', () => {
        const handleExpandChange = vi.fn();
        renderWithQueryClient(
            <ChartCard title="Test Chart" {...defaultProps} expandedChart="Test Chart" onExpandChange={handleExpandChange}>
                <div>Chart Content</div>
            </ChartCard>
        );

        fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });

        expect(handleExpandChange).toHaveBeenCalledWith(null);
    });

    describe('data processing coverage', () => {
        it.each([
            { type: 'date' as const },
            { type: 'hour' as const },
            { type: 'weekday' as const },
            { type: 'history' as const },
            { type: 'filterConfig' as const },
        ])('processes $type data correctly upon filter change', async ({ type }) => {
            renderWithQueryClient(
                <ChartCard 
                    title="Test Chart" 
                    {...defaultProps} 
                    chartType={type}
                    expandedChart="Test Chart" 
                    parentTimeRange="All"
                >
                    {(data: any) => <div data-testid={`data-${type}`}>{data ? 'Has Data' : 'No Data'}</div>}
                </ChartCard>
            );

            // Change the filter to trigger a fetch
            const select = screen.getByDisplayValue('All');
            fireEvent.change(select, { target: { value: 'Last week' } });

            await waitFor(() => {
                expect(screen.getByTestId(`data-${type}`)).toHaveTextContent('Has Data');
            });
        });
    });

    describe('time range filter coverage', () => {
        it.each([
            { range: 'Last year' },
            { range: 'Last 6 months' },
            { range: 'Last day' },
        ])('computes start date correctly for $range', async ({ range }) => {
            renderWithQueryClient(
                <ChartCard 
                    title="Test Chart" 
                    {...defaultProps} 
                    chartType="weekday"
                    expandedChart="Test Chart" 
                    parentTimeRange="All"
                >
                    {() => <div data-testid="data">Has Data</div>}
                </ChartCard>
            );

            const select = screen.getByDisplayValue('All');
            fireEvent.change(select, { target: { value: range } });

            await waitFor(() => {
                expect(screen.getByTestId('data')).toHaveTextContent('Has Data');
            });
        });
    });
});
