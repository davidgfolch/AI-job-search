import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import KeywordChart from '../KeywordChart';

vi.mock('recharts', () => ({
    ComposedChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Bar: () => null,
    Line: () => null,
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
    it('renders the duplicate table with job ids', () => {
        render(<KeywordChart rows={rows} />);
        expect(screen.getByText('Already-in-DB duplicates by keyword')).toBeInTheDocument();
        expect(screen.getByText('91,92')).toBeInTheDocument();
        expect(screen.getByRole('columnheader', { name: 'Duplicate ids' })).toBeInTheDocument();
    });

    it('renders a helpful message when there is no data', () => {
        render(<KeywordChart rows={[]} />);
        expect(screen.getByText(/No keyword search data/)).toBeInTheDocument();
    });

    it('renders the no-duplicates message when all rows have zero duplicates', () => {
        render(<KeywordChart rows={[{ ...rows[0], duplicates: 0, duplicate_ids: '' }]} />);
        expect(screen.getByText(/No already-in-DB duplicates/)).toBeInTheDocument();
    });
});
