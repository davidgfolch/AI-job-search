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
        expect(data[0]['new:Indeed|python']).toBe(18);
        expect(data[0]['dupes:Indeed|python']).toBe(2);
        expect(data[1]['total:Indeed|python']).toBe(50);
        expect(data[0]['dupes:Indeed|java']).toBe(0);
    });

    it('returns empty data for no rows', () => {
        expect(buildKeywordChartData([])).toEqual({ data: [], series: [] });
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
