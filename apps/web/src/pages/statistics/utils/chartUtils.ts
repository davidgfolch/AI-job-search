const COLORS_PALETTE = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00C49F', 
    '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57', '#a05195', '#d45087'
];

export const getColorForSource = (source: string, allSources: string[]): string => {
    // Generate a consistent index based on the source name string
    let hash = 0;
    for (let i = 0; i < source.length; i++) {
        hash = source.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % COLORS_PALETTE.length;
    return COLORS_PALETTE[index];
};

export function pivotData<T>(data: T[] | undefined, xKey: keyof T, seriesKey: keyof T, valueKey: keyof T): Record<string, any>[] {
    if (!data) return [];
    const result: Record<string, any>[] = [];
    const map = new Map<string, Record<string, any>>();
    
    data.forEach(item => {
        const xVal = String(item[xKey]);
        if (!map.has(xVal)) {
            const newEntry: Record<string, any> = { [String(xKey)]: item[xKey] };
            map.set(xVal, newEntry);
            result.push(newEntry);
        }
        const seriesVal = String(item[seriesKey]);
        const value = item[valueKey];
        const entry = map.get(xVal);
        if (entry) {
            entry[seriesVal] = value;
        }
    });

    return result.sort((a, b) => {
        const valA = a[String(xKey)];
        const valB = b[String(xKey)];
        return valA > valB ? 1 : -1;
    });
}

export function getSeriesKeys(data: Record<string, any>[], ignoreKeys: string[] = ['dateCreated', 'hour', 'weekday']): string[] {
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

/**
 * Processes data to unify small sources into "Other"
 * @param data Raw data array
 * @param xKey Key to group by on X axis
 * @param seriesKey Key that determines the series (source)
 * @param valueKey Key for the numeric value
 * @param maxSources Maximum number of distinct sources to show individually
 */
export function processChartData<T>(
    data: T[] | undefined, 
    xKey: keyof T, 
    seriesKey: keyof T, 
    valueKey: keyof T,
    maxSources: number = 7
): { processedData: Record<string, any>[], keys: string[] } {
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
    const processed: Record<string, any>[] = [];
    const map = new Map<string, Record<string, any>>();
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
            const newEntry: Record<string, any> = { [String(xKey)]: item[xKey] };
            if (hasOther) { 
                newEntry['otherDetails'] = {}; // Initialize container
            }
            map.set(xVal, newEntry);
            processed.push(newEntry);
        }
        
        const entry = map.get(xVal)!;
        entry[sourceKey] = (entry[sourceKey] || 0) + val;
        
        if (sourceKey === 'Other') {
             entry['otherDetails'] = otherDetailsMap.get(xVal);
        }
    });

    // 4. Return formatted data and keys
    const resultKeys = Array.from(topSources);
    if (hasOther) resultKeys.push('Other');

    const sortedData = processed.sort((a, b) => {
        const valA = a[String(xKey)];
        const valB = b[String(xKey)];
        return valA > valB ? 1 : -1;
    });

    return { processedData: sortedData, keys: resultKeys };
}
