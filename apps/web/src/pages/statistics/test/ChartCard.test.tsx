import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ChartCard from '../components/ChartCard';
import '@testing-library/jest-dom';

describe('ChartCard', () => {
    it('renders correctly with title and children', () => {
        render(
            <ChartCard title="Test Chart">
                <div data-testid="chart-content">Chart Content</div>
            </ChartCard>
        );

        expect(screen.getByText('Test Chart')).toBeInTheDocument();
        expect(screen.getByTestId('chart-content')).toBeInTheDocument();
        expect(screen.queryByTitle('Expand to Full Screen')).toBeInTheDocument();
    });

    it('renders with complex children', () => {
        render(
            <ChartCard title="Salary Distribution">
                <div>
                    <div data-testid="chart-canvas">Chart Canvas</div>
                    <div data-testid="chart-legend">Chart Legend</div>
                </div>
            </ChartCard>
        );

        expect(screen.getByText('Salary Distribution')).toBeInTheDocument();
        expect(screen.getByTestId('chart-canvas')).toBeInTheDocument();
        expect(screen.getByTestId('chart-legend')).toBeInTheDocument();
    });

    it('renders with special characters in title', () => {
        render(
            <ChartCard title="Jobs in 2024 (Q1-Q2)">
                <div>Content</div>
            </ChartCard>
        );

        expect(screen.getByText('Jobs in 2024 (Q1-Q2)')).toBeInTheDocument();
    });

    it('toggles expand state correctly', () => {
        const { container } = render(
            <ChartCard title="Test Chart">
                <div>Chart Content</div>
            </ChartCard>
        );

        const expandButton = screen.getByTitle('Expand to Full Screen');
        const section = container.querySelector('section');

        expect(section).not.toHaveClass('expanded');

        fireEvent.click(expandButton);

        expect(section).toHaveClass('expanded');
        expect(screen.getByTitle('Close Full Screen')).toBeInTheDocument();

        fireEvent.click(screen.getByTitle('Close Full Screen'));

        expect(section).not.toHaveClass('expanded');
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
            expect(() => render(<ChartCard title={title}>{children}</ChartCard>)).not.toThrow();
        });
    });
});