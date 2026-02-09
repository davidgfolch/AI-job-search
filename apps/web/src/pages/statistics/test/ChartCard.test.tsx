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
});
