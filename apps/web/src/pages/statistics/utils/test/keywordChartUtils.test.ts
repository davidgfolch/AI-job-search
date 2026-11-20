import { describe, it, expect } from 'vitest';
import type { ChartDataset } from '../chartUtils';
import { buildKeywordChartData } from '../keywordChartUtils';

const rows = [
    { date: '2026-11-19', site: 'Indeed', keyword: 'python', reported_total: 40, processed: 20, new: 18, duplicates: 2, duplicate_ids: '1,2' },
    { date: '2026-11-19', site: 'Indeed', keyword: 'java', reported_total: 10, processed: 5, new: 5, duplicates: 0, duplicate_ids: '' },
    { date: '2026-11-20', site: 'Indeed', keyword: 'python', reported_total: 50, processed: 30, new: 25, duplicates: 5, duplicate_ids: '1,3,4,5,6' },
] as ChartDataset;

describe('buildKeywordChartData', () => {
    it('creates one date row with only new-job fields per keyword', () => {
        const { data, series } = buildKeywordChartData(rows);
        expect(series).toHaveLength(2);
        expect(data.map(row => row.date)).toEqual(['2026-11-19', '2026-11-20']);
        expect(data[0]['new:python']).toBe(18);
        expect(data[1]['new:python']).toBe(25);
        expect(data[0]['new:java']).toBe(5);
        expect(data[0]['dupes:python']).toBeUndefined();
        expect(data[0]['total:python']).toBeUndefined();
    });

    it('returns empty data for no rows', () => {
        expect(buildKeywordChartData([])).toEqual({ data: [], series: [] });
    });

    it('aggregates the same keyword across sites for (All) view', () => {
        const mixed = [
            { date: '2026-11-19', site: 'Linkedin', keyword: 'java', reported_total: 10, processed: 10, new: 3, duplicates: 7 },
            { date: '2026-11-19', site: 'Infojobs', keyword: 'java', reported_total: 5, processed: 5, new: 1, duplicates: 4 },
        ] as ChartDataset;
        const { data, series } = buildKeywordChartData(mixed);
        expect(series.map(s => s.label)).toEqual(['java']);
        expect(data[0]['new:java']).toBe(4);
    });

    it('drops all-zero rows so empty sites/keywords do not render', () => {
        const mixed = [
            { date: '2026-11-19', site: 'Stub', keyword: 'java', reported_total: 0, processed: 0, new: 0, duplicates: 0 },
            { date: '2026-11-19', site: 'Linkedin', keyword: 'java', reported_total: 10, processed: 10, new: 3, duplicates: 7 },
        ] as ChartDataset;
        const { series } = buildKeywordChartData(mixed);
        expect(series.map(s => s.label)).toEqual(['java']);
    });

    it('drops keywords with no new jobs even when other metrics are present', () => {
        const mixed = [
            { date: '2026-11-19', site: 'Linkedin', keyword: 'java', reported_total: 10, processed: 10, new: 0, duplicates: 10 },
        ] as ChartDataset;
        expect(buildKeywordChartData(mixed)).toEqual({ data: [], series: [] });
    });

    it('caps to the most recent maxDates', () => {
        const manyDates = Array.from({ length: 40 }, (_, i) => {
            const d = new Date(2026, 0, 1 + i);
            const date = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
            return { date, site: 'Linkedin', keyword: 'java', reported_total: 1, processed: 1, new: 1, duplicates: 0 };
        }) as ChartDataset;
        const { data } = buildKeywordChartData(manyDates, 30);
        expect(data).toHaveLength(30);
        expect(data[0].date).toBe('2026-01-11');
        expect(data[29].date).toBe('2026-02-09');
    });

    it('keeps only the top maxSeries keywords by new-job volume', () => {
        const many = [
            { date: '2026-11-19', site: 'Linkedin', keyword: 'big', reported_total: 100, processed: 100, new: 50, duplicates: 50 },
            { date: '2026-11-19', site: 'Linkedin', keyword: 'small', reported_total: 1, processed: 1, new: 1, duplicates: 0 },
            { date: '2026-11-19', site: 'Linkedin', keyword: 'medium', reported_total: 10, processed: 10, new: 5, duplicates: 5 },
        ] as ChartDataset;
        const { series } = buildKeywordChartData(many, 30, 2);
        expect(series.map(s => s.label)).toEqual(['big', 'medium']);
    });
});
