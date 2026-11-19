import { describe, it, expect } from 'vitest';
import type { ChartDataset } from '../chartUtils';
import { buildKeywordChartData, keywordRowsWithDuplicates } from '../keywordChartUtils';

const rows = [
    { date: '2026-11-19', site: 'Indeed', keyword: 'python', reported_total: 40, processed: 20, new: 18, duplicates: 2, duplicate_ids: '1,2' },
    { date: '2026-11-19', site: 'Indeed', keyword: 'java', reported_total: 10, processed: 5, new: 5, duplicates: 0, duplicate_ids: '' },
    { date: '2026-11-20', site: 'Indeed', keyword: 'python', reported_total: 50, processed: 30, new: 25, duplicates: 5, duplicate_ids: '1,3,4,5,6' },
] as ChartDataset;

describe('buildKeywordChartData', () => {
    it('creates one date row with stacked and line fields per keyword', () => {
        const { data, series } = buildKeywordChartData(rows);
        expect(series).toHaveLength(2);
        expect(data.map(row => row.date)).toEqual(['2026-11-19', '2026-11-20']);
        expect(data[0]['new:python']).toBe(18);
        expect(data[0]['dupes:python']).toBe(2);
        expect(data[1]['total:python']).toBe(50);
        expect(data[0]['dupes:java']).toBe(0);
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
        expect(data[0]['dupes:java']).toBe(11);
        expect(data[0]['total:java']).toBe(15);
    });

    it('drops all-zero rows so empty sites/keywords do not render', () => {
        const mixed = [
            { date: '2026-11-19', site: 'Stub', keyword: 'java', reported_total: 0, processed: 0, new: 0, duplicates: 0 },
            { date: '2026-11-19', site: 'Linkedin', keyword: 'java', reported_total: 10, processed: 10, new: 3, duplicates: 7 },
        ] as ChartDataset;
        const { series } = buildKeywordChartData(mixed);
        expect(series.map(s => s.label)).toEqual(['java']);
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

    it('keeps only the top maxSeries keywords by volume', () => {
        const many = [
            { date: '2026-11-19', site: 'Linkedin', keyword: 'big', reported_total: 100, processed: 100, new: 50, duplicates: 50 },
            { date: '2026-11-19', site: 'Linkedin', keyword: 'small', reported_total: 1, processed: 1, new: 1, duplicates: 0 },
            { date: '2026-11-19', site: 'Linkedin', keyword: 'medium', reported_total: 10, processed: 10, new: 5, duplicates: 5 },
        ] as ChartDataset;
        const { series } = buildKeywordChartData(many, 30, 2);
        expect(series.map(s => s.label)).toEqual(['big', 'medium']);
    });
});

describe('keywordRowsWithDuplicates', () => {
    it('keeps only duplicate rows sorted by date', () => {
        const result = keywordRowsWithDuplicates(rows);
        expect(result).toHaveLength(2);
        expect(result[0]).toMatchObject({ date: '2026-11-19', keyword: 'python', duplicates: 2, duplicate_ids: '1,2' });
        expect(result[1].date).toBe('2026-11-20');
    });
});
