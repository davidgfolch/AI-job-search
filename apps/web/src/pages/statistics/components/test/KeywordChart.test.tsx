import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import KeywordChart from '../KeywordChart';

vi.mock('recharts', () => ({
    LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
    Bar: () => <div data-testid="chart-bar" />,
    Line: ({ name }: { name?: string }) => <div data-testid="chart-line" data-name={name} />,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const rows = [
    { date: '2026-11-19', site: 'Indeed', keyword: 'python', reported_total: 40, processed: 20, new: 18, duplicates: 2, duplicate_ids: '91,92' },
] as any;

describe('KeywordChart', () => {
    it('renders one line per keyword with no duplicate or reported series', () => {
        render(<KeywordChart rows={rows} />);
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
        expect(screen.getAllByTestId('chart-line')).toHaveLength(1);
        expect(screen.getByTestId('chart-line')).toHaveAttribute('data-name', 'python');
        expect(screen.queryByTestId('chart-bar')).not.toBeInTheDocument();
    });

    it('does not render the duplicates section', () => {
        render(<KeywordChart rows={rows} />);
        expect(screen.queryByText('Already-in-DB duplicates by keyword')).not.toBeInTheDocument();
        expect(screen.queryByText('91,92')).not.toBeInTheDocument();
    });

    it('renders a helpful message when there is no data', () => {
        render(<KeywordChart rows={[]} />);
        expect(screen.getByText(/No keyword search data/)).toBeInTheDocument();
    });
});
