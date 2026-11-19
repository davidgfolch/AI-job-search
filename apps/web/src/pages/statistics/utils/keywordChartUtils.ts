import { getColorForSource, type ChartDataset, type ChartRow } from './chartUtils';

export interface KeywordSeries {
    key: string;
    label: string;
    newKey: string;
    duplicateKey: string;
    totalKey: string;
    color: string;
}

const seriesKey = (row: ChartRow) => `${row.site ?? ''}|${row.keyword ?? ''}`;

/** Pivots keyword stats into one x-axis point per date with stacked new/duplicate bars and a reported-total line per keyword. */
export function buildKeywordChartData(rows: ChartDataset): { data: ChartDataset; series: KeywordSeries[] } {
    const dates = Array.from(new Set(rows.map(row => String(row.date ?? '')))).filter(Boolean).sort();
    const keys = Array.from(new Set(rows.map(seriesKey))).filter(key => key !== '|');
    const series: KeywordSeries[] = keys.map(key => {
        const [site, keyword] = key.split('|');
        return {
            key, label: `${site} · ${keyword}`, newKey: `new:${key}`, duplicateKey: `dupes:${key}`,
            totalKey: `total:${key}`, color: getColorForSource(key)
        };
    });
    const data: ChartDataset = dates.map(date => {
        const row: ChartRow = { date };
        series.forEach(item => {
            const match = rows.find(candidate => String(candidate.date ?? '') === date && seriesKey(candidate) === item.key);
            row[item.newKey] = Number(match?.new ?? 0);
            row[item.duplicateKey] = Number(match?.duplicates ?? 0);
            row[item.totalKey] = Number(match?.reported_total ?? 0);
        });
        return row;
    });
    return { data, series };
}

export interface DuplicateRow {
    date: string;
    site: string;
    keyword: string;
    duplicates: number;
    duplicate_ids: string;
}

export function keywordRowsWithDuplicates(rows: ChartDataset): DuplicateRow[] {
    return rows
        .filter(row => Number(row.duplicates ?? 0) > 0)
        .map(row => ({
            date: String(row.date ?? ''), site: String(row.site ?? ''), keyword: String(row.keyword ?? ''),
            duplicates: Number(row.duplicates ?? 0), duplicate_ids: String(row.duplicate_ids ?? '')
        }))
        .sort((a, b) => a.date.localeCompare(b.date) || a.site.localeCompare(b.site) || a.keyword.localeCompare(b.keyword));
}
