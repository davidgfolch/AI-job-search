/** A single cell of a chart row: an axis value, a series total or the breakdown of the "Other" bucket. */
export type ChartCell = string | number | Record<string, number> | undefined;
/** A chart row keyed by axis name, series name and, when present, the "Other" breakdown. */
export type ChartRow = Record<string, ChartCell>;
export type ChartDataset = ChartRow[];

const COLORS_PALETTE = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00C49F', 
    '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57', '#a05195', '#d45087'
];

export const getColorForSource = (source: string): string => {
    // Generate a consistent index based on the source name string
    let hash = 0;
    for (let i = 0; i < source.length; i++) {
        hash = source.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % COLORS_PALETTE.length;
    return COLORS_PALETTE[index];
};

/** Orders two axis values the way the JavaScript comparison operator does: numerically for numbers and
 * lexicographically for strings. */
const compareChartCells = (left: ChartCell, right: ChartCell): number => {
    if (typeof left === 'number' && typeof right === 'number') return left > right ? 1 : -1;
    if (typeof left === 'string' && typeof right === 'string') return left > right ? 1 : -1;
    return Number(left) > Number(right) ? 1 : -1;
};

export function pivotData<T>(data: T[] | undefined, xKey: keyof T, seriesKey: keyof T, valueKey: keyof T): ChartDataset {
    if (!data) return [];
    const result: ChartDataset = [];
    const map = new Map<string, ChartRow>();

    data.forEach(item => {
        const xVal = String(item[xKey]);
        if (!map.has(xVal)) {
            const newEntry: ChartRow = { [String(xKey)]: item[xKey] as ChartCell };
            map.set(xVal, newEntry);
            result.push(newEntry);
        }
        const seriesVal = String(item[seriesKey]);
        const value = item[valueKey] as ChartCell;
        const entry = map.get(xVal);
        if (entry) {
            entry[seriesVal] = value;
        }
    });

    return result.sort((a, b) => compareChartCells(a[String(xKey)], b[String(xKey)]));
}

export function getSeriesKeys(data: ChartDataset | undefined, ignoreKeys: string[] = ['dateCreated', 'hour', 'weekday']): string[] {
    if (!data) return [];
    const keys = new Set<string>();
    data.forEach(item => {
        Object.keys(item).forEach(key => {
            if (!ignoreKeys.includes(key)) {
                keys.add(key);
            }
        });
    });
    return Array.from(keys).sort();
}

export function getDateRange(timeRange: string): { startDate: string | undefined; endDate: string | undefined } {
    if (timeRange === 'All') return { startDate: undefined, endDate: undefined };
    const end = new Date();
    const start = new Date();
    if (timeRange === 'Last year') {
        start.setFullYear(start.getFullYear() - 1);
    } else if (timeRange === 'Last 6 months') {
        start.setMonth(start.getMonth() - 6);
    } else if (timeRange === 'Last 3 months') {
        start.setMonth(start.getMonth() - 3);
    } else if (timeRange === 'Last month') {
        start.setMonth(start.getMonth() - 1);
    } else if (timeRange === 'Last week') {
        start.setDate(start.getDate() - 7);
    } else if (timeRange === 'Last day') {
        start.setDate(start.getDate() - 1);
    }
    return { startDate: start.toISOString().split('T')[0], endDate: end.toISOString().split('T')[0] };
}

export function processChartData<T>(
    data: T[] | undefined, 
    xKey: keyof T, 
    seriesKey: keyof T, 
    valueKey: keyof T,
    maxSources: number = 7
): { processedData: ChartDataset, keys: string[] } {
    if (!data) return { processedData: [], keys: [] };

    // 1. Calculate total volume per source to identify top sources
    const sourceTotals = new Map<string, number>();
    data.forEach(item => {
        const source = String(item[seriesKey]);
        const val = Number(item[valueKey]) || 0;
        sourceTotals.set(source, (sourceTotals.get(source) || 0) + val);
    });

    // 2. Identify top sources
    const sortedSources = Array.from(sourceTotals.entries())
        .sort((a, b) => b[1] - a[1])
        .map(entry => entry[0]);
    
    const topSources = new Set(sortedSources.slice(0, maxSources));
    const hasOther = sortedSources.length > maxSources;

    // 3. Transform data with "Other" grouping
    const processed: ChartDataset = [];
    const map = new Map<string, ChartRow>();
    const otherDetailsMap = new Map<string, Record<string, number>>();

    data.forEach(item => {
        const xVal = String(item[xKey]);
        const rawSource = String(item[seriesKey]);
        const val = Number(item[valueKey]) || 0;
        
        let sourceKey = rawSource;
        if (!topSources.has(rawSource)) {
            sourceKey = 'Other';
            // Store details for tooltip
            if (!otherDetailsMap.has(xVal)) {
                otherDetailsMap.set(xVal, {});
            }
            const details = otherDetailsMap.get(xVal)!;
            details[rawSource] = (details[rawSource] || 0) + val;
        }

        if (!map.has(xVal)) {
            const newEntry: ChartRow = { [String(xKey)]: item[xKey] as ChartCell };
            if (hasOther) { 
                newEntry['otherDetails'] = {}; // Initialize container
            }
            map.set(xVal, newEntry);
            processed.push(newEntry);
        }
        
        const entry = map.get(xVal)!;
        const current = entry[sourceKey];
        entry[sourceKey] = (typeof current === 'number' ? current : 0) + val;
        
        if (sourceKey === 'Other') {
             entry['otherDetails'] = otherDetailsMap.get(xVal);
        }
    });

    // 4. Return formatted data and keys
    const resultKeys = Array.from(topSources);
    if (hasOther) resultKeys.push('Other');

    const sortedData = processed.sort((a, b) => compareChartCells(a[String(xKey)], b[String(xKey)]));

    return { processedData: sortedData, keys: resultKeys };
}
