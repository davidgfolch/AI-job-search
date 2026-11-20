import { getColorForSource, type ChartDataset, type ChartRow } from './chartUtils';

export interface KeywordSeries {
    key: string;
    label: string;
    newKey: string;
    color: string;
}

const num = (value: ChartRow[string]) => Number(value ?? 0);
const rowVolume = (row: ChartRow) => num(row.new);

const aggregateByDateKeyword = (rows: ChartDataset): ChartDataset => {
    const map = new Map<string, ChartRow>();
    rows.forEach(row => {
        const date = String(row.date ?? '');
        const keyword = String(row.keyword ?? '');
        if (!date || !keyword) return;
        const key = `${date}|${keyword}`;
        const current = map.get(key) ?? { date, keyword, new: 0 };
        current.new = num(current.new) + num(row.new);
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

/** Aggregates new jobs by date and keyword, capping dates/series for readability. */
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
        key: keyword, label: keyword, newKey: `new:${keyword}`, color: getColorForSource(keyword)
    }));
    const data: ChartDataset = dates.map(date => {
        const row: ChartRow = { date };
        series.forEach(item => {
            const match = aggregated.find(candidate => String(candidate.date ?? '') === date && String(candidate.keyword ?? '') === item.key);
            row[item.newKey] = num(match?.new);
        });
        return row;
    });
    return { data, series };
}
