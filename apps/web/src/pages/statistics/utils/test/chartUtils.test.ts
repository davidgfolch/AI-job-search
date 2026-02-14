import { describe, it, expect } from 'vitest';
import { getColorForSource, pivotData, getSeriesKeys, processChartData } from '../chartUtils';

describe('chartUtils', () => {
    describe('getColorForSource', () => {
        it('returns consistent color for same source', () => {
            const color1 = getColorForSource('LinkedIn', ['LinkedIn', 'Indeed']);
            const color2 = getColorForSource('LinkedIn', ['LinkedIn', 'Indeed']);
            expect(color1).toBe(color2);
        });

        it('returns different colors for different sources', () => {
            const color1 = getColorForSource('LinkedIn', ['LinkedIn', 'Indeed']);
            const color2 = getColorForSource('Indeed', ['LinkedIn', 'Indeed']);
            expect(color1).not.toBe(color2);
        });

        it('handles empty source string', () => {
            const color = getColorForSource('', ['LinkedIn']);
            expect(color).toBeDefined();
        });

        it('handles long source names', () => {
            const longName = 'A'.repeat(100);
            const color = getColorForSource(longName, [longName]);
            expect(color).toBeDefined();
        });
    });

    describe('pivotData', () => {
        it('returns empty array for undefined data', () => {
            const result = pivotData(undefined, 'date', 'source', 'count');
            expect(result).toEqual([]);
        });

        it('returns empty array for empty array', () => {
            const result = pivotData([], 'date', 'source', 'count');
            expect(result).toEqual([]);
        });

        it('pivots data correctly', () => {
            const data = [
                { date: '2024-01-01', source: 'LinkedIn', count: 10 },
                { date: '2024-01-01', source: 'Indeed', count: 5 },
                { date: '2024-01-02', source: 'LinkedIn', count: 8 },
            ];
            const result = pivotData(data, 'date', 'source', 'count');
            expect(result).toHaveLength(2);
            expect(result[0]).toHaveProperty('LinkedIn', 10);
            expect(result[0]).toHaveProperty('Indeed', 5);
            expect(result[1]).toHaveProperty('LinkedIn', 8);
        });

        it('sorts results by xKey', () => {
            const data = [
                { date: '2024-01-02', source: 'LinkedIn', count: 8 },
                { date: '2024-01-01', source: 'LinkedIn', count: 10 },
            ];
            const result = pivotData(data, 'date', 'source', 'count');
            expect(result[0].date).toBe('2024-01-01');
            expect(result[1].date).toBe('2024-01-02');
        });

    it('overwrites value for same xKey and seriesKey', () => {
        const data = [
            { date: '2024-01-01', source: 'LinkedIn', count: 10 },
            { date: '2024-01-01', source: 'LinkedIn', count: 5 },
        ];
        const result = pivotData(data, 'date', 'source', 'count');
        expect(result[0].LinkedIn).toBe(5);
    });
    });

    describe('getSeriesKeys', () => {
        it('returns empty array for undefined data', () => {
            const keys = getSeriesKeys(undefined);
            expect(keys).toEqual([]);
        });

        it('returns empty array for empty array', () => {
            const keys = getSeriesKeys([]);
            expect(keys).toEqual([]);
        });

        it('extracts series keys excluding ignored keys', () => {
            const data = [
                { dateCreated: '2024-01-01', LinkedIn: 10, Indeed: 5 },
                { dateCreated: '2024-01-02', LinkedIn: 8 },
            ];
            const keys = getSeriesKeys(data);
            expect(keys).toContain('LinkedIn');
            expect(keys).toContain('Indeed');
            expect(keys).not.toContain('dateCreated');
        });

        it('sorts keys alphabetically', () => {
            const data = [
                { dateCreated: '2024-01-01', z_source: 10, a_source: 5 },
            ];
            const keys = getSeriesKeys(data);
            expect(keys).toEqual(['a_source', 'z_source']);
        });

        it('allows custom ignore keys', () => {
            const data = [
                { dateCreated: '2024-01-01', custom: 10, LinkedIn: 5 },
            ];
            const keys = getSeriesKeys(data, ['dateCreated', 'custom']);
            expect(keys).toEqual(['LinkedIn']);
        });
    });

    describe('processChartData', () => {
        it('returns empty for undefined data', () => {
            const result = processChartData(undefined, 'date', 'source', 'count');
            expect(result.processedData).toEqual([]);
            expect(result.keys).toEqual([]);
        });

        it('returns empty for empty array', () => {
            const result = processChartData([], 'date', 'source', 'count');
            expect(result.processedData).toEqual([]);
            expect(result.keys).toEqual([]);
        });

        it('groups data by xKey and seriesKey', () => {
            const data = [
                { date: '2024-01-01', source: 'LinkedIn', count: 10 },
                { date: '2024-01-01', source: 'Indeed', count: 5 },
                { date: '2024-01-02', source: 'LinkedIn', count: 8 },
            ];
            const result = processChartData(data, 'date', 'source', 'count');
            expect(result.processedData).toHaveLength(2);
            expect(result.keys).toContain('LinkedIn');
            expect(result.keys).toContain('Indeed');
        });

        it('limits to maxSources and groups others as Other', () => {
            const data = [
                { date: '2024-01-01', source: 'Source1', count: 100 },
                { date: '2024-01-01', source: 'Source2', count: 90 },
                { date: '2024-01-01', source: 'Source3', count: 80 },
                { date: '2024-01-01', source: 'Source4', count: 70 },
                { date: '2024-01-01', source: 'Source5', count: 60 },
                { date: '2024-01-01', source: 'Source6', count: 50 },
                { date: '2024-01-01', source: 'Source7', count: 40 },
                { date: '2024-01-01', source: 'Source8', count: 30 },
            ];
            const result = processChartData(data, 'date', 'source', 'count', 7);
            expect(result.keys).toContain('Other');
            expect(result.keys).not.toContain('Source8');
        });

        it('sorts results by xKey', () => {
            const data = [
                { date: '2024-01-02', source: 'LinkedIn', count: 8 },
                { date: '2024-01-01', source: 'LinkedIn', count: 10 },
            ];
            const result = processChartData(data, 'date', 'source', 'count');
            expect(result.processedData[0].date).toBe('2024-01-01');
            expect(result.processedData[1].date).toBe('2024-01-02');
        });

        it('handles numeric values correctly', () => {
            const data = [
                { hour: 1, source: 'LinkedIn', count: '10' },
                { hour: 1, source: 'Indeed', count: null },
            ];
            const result = processChartData(data, 'hour', 'source', 'count');
            expect(result.processedData[0].LinkedIn).toBe(10);
            expect(result.processedData[0].Indeed).toBe(0);
        });

        it('does not add Other when within maxSources', () => {
            const data = [
                { date: '2024-01-01', source: 'LinkedIn', count: 100 },
                { date: '2024-01-01', source: 'Indeed', count: 50 },
            ];
            const result = processChartData(data, 'date', 'source', 'count', 7);
            expect(result.keys).not.toContain('Other');
        });

        it('adds otherDetails when Other exists', () => {
            const data = [
                { date: '2024-01-01', source: 'Source1', count: 100 },
                { date: '2024-01-01', source: 'Source2', count: 90 },
                { date: '2024-01-01', source: 'Source3', count: 80 },
                { date: '2024-01-01', source: 'Source4', count: 70 },
                { date: '2024-01-01', source: 'Source5', count: 60 },
                { date: '2024-01-01', source: 'Source6', count: 50 },
                { date: '2024-01-01', source: 'Source7', count: 40 },
                { date: '2024-01-01', source: 'Source8', count: 30 },
            ];
            const result = processChartData(data, 'date', 'source', 'count', 7);
            expect(result.processedData[0]).toHaveProperty('otherDetails');
        });
    });
});
