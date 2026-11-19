import { getColorForSource, type ChartDataset, type ChartRow } from './chartUtils';

export interface KeywordSeries {
    key: string;
    label: string;
    newKey: string;
    duplicateKey: string;
    totalKey: string;
    color: string;
}

const num = (value: ChartRow[string]) => Number(value ?? 0);
const rowVolume = (row: ChartRow) => num(row.reported_total) + num(row.processed) + num(row.new) + num(row.duplicates);

const aggregateByDateKeyword = (rows: ChartDataset): ChartDataset => {
    const map = new Map<string, ChartRow>();
    rows.forEach(row => {
        const date = String(row.date ?? '');
        const keyword = String(row.keyword ?? '');
        if (!date || !keyword) return;
        const key = `${date}|${keyword}`;
        const current = map.get(key) ?? { date, keyword, reported_total: 0, processed: 0, new: 0, duplicates: 0 };
        current.reported_total = num(current.reported_total) + num(row.reported_total);
        current.processed = num(current.processed) + num(row.processed);
        current.new = num(current.new) + num(row.new);
        current.duplicates = num(current.duplicates) + num(row.duplicates);
        map.set(key, current);
    });
    return Array.from(map.values());
};

const keepTopSeries = (rows: ChartDataset, maxSeries: number): ChartDataset => {
    const totals = new Map<string, number>();
    rows.forEach(row => {
        const keyword = String(row.keyword ?? '');
        totals.set(keyword, (totals.get(keyword) ?? 0) + rowVolume(row));
    });
    const top = new Set(Array.from(totals.entries()).sort((a, b) => b[1] - a[1]).slice(0, maxSeries).map(([keyword]) => keyword));
    return rows.filter(row => top.has(String(row.keyword ?? '')));
};

/** Aggregates keyword stats by date and keyword, capping dates/series for readability. */
export function buildKeywordChartData(rows: ChartDataset, maxDates = 30, maxSeries = 8): { data: ChartDataset; series: KeywordSeries[] } {
    const active = rows.filter(row => rowVolume(row) > 0);
    let aggregated = aggregateByDateKeyword(active);
    aggregated = keepTopSeries(aggregated, maxSeries);
    const allDates = Array.from(new Set(aggregated.map(row => String(row.date ?? '')))).filter(Boolean).sort();
    const dates = allDates.slice(-maxDates);
    const dateSet = new Set(dates);
    aggregated = aggregated.filter(row => dateSet.has(String(row.date ?? '')));
    const keywords = Array.from(new Set(aggregated.map(row => String(row.keyword ?? '')))).filter(Boolean).sort();
    const series: KeywordSeries[] = keywords.map(keyword => ({
        key: keyword, label: keyword, newKey: `new:${keyword}`, duplicateKey: `dupes:${keyword}`,
        totalKey: `total:${keyword}`, color: getColorForSource(keyword)
    }));
    const data: ChartDataset = dates.map(date => {
        const row: ChartRow = { date };
        series.forEach(item => {
            const match = aggregated.find(candidate => String(candidate.date ?? '') === date && String(candidate.keyword ?? '') === item.key);
            row[item.newKey] = num(match?.new);
            row[item.duplicateKey] = num(match?.duplicates);
            row[item.totalKey] = num(match?.reported_total);
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
