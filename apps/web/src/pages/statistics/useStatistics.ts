import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday, getFilterConfigStats, getKeywordStats } from './api/StatisticsApi';
import type { SourceDateStat, SourceHourStat, SourceWeekdayStat } from './api/StatisticsApi';
import { processChartData, getDateRange, type ChartDataset } from './utils/chartUtils';
import { ALL_SITES, DEFAULT_SITE, KEYWORD_SITES, SCRAPER_SITES } from './sites';

const allowedSet = new Set<string>(SCRAPER_SITES);
const keywordAllowedSet = new Set<string>(KEYWORD_SITES);

export const useStatistics = () => {
    const [timeRange, setTimeRange] = React.useState('Last 3 months');
    const [includeOldJobs, setIncludeOldJobs] = React.useState(true);
    const [site, setSite] = React.useState(DEFAULT_SITE);

    const { startDate, endDate } = React.useMemo(() => getDateRange(timeRange), [timeRange]);

    const { data: historyData } = useQuery({ queryKey: ['statistics', 'history', startDate, endDate, includeOldJobs], queryFn: () => getHistoryStats(startDate, endDate, includeOldJobs) });
    const { data: sourcesDateData } = useQuery({ queryKey: ['statistics', 'sourcesDate', startDate, endDate, includeOldJobs], queryFn: () => getSourcesByDate(startDate, endDate, includeOldJobs) });
    const { data: sourcesHourData } = useQuery({ queryKey: ['statistics', 'sourcesHour', startDate, endDate, includeOldJobs], queryFn: () => getSourcesByHour(startDate, endDate, includeOldJobs) });
    const { data: sourcesWeekdayData } = useQuery({ queryKey: ['statistics', 'sourcesWeekday', startDate, endDate, includeOldJobs], queryFn: () => getSourcesByWeekday(startDate, endDate, includeOldJobs) });
    // The filter-configs and keyword endpoints do not take includeOldJobs, so it is not part of the cache key.
    const { data: filterConfigData } = useQuery({ queryKey: ['statistics', 'filterConfigs', startDate, endDate], queryFn: () => getFilterConfigStats(startDate, endDate) });
    const { data: keywordStats } = useQuery({ queryKey: ['statistics', 'keyword', startDate, endDate], queryFn: () => getKeywordStats(startDate, endDate) });

    const sourcesDateFiltered = React.useMemo(() => {
        const rows = (sourcesDateData || []).filter(row => allowedSet.has(row.source));
        return site === ALL_SITES ? rows : rows.filter(row => row.source === site);
    }, [sourcesDateData, site]);
    const sourcesHourFiltered = React.useMemo(() => {
        const rows = (sourcesHourData || []).filter(row => allowedSet.has(row.source));
        return site === ALL_SITES ? rows : rows.filter(row => row.source === site);
    }, [sourcesHourData, site]);
    const sourcesWeekdayFiltered = React.useMemo(() => {
        const rows = (sourcesWeekdayData || []).filter(row => allowedSet.has(row.source));
        return site === ALL_SITES ? rows : rows.filter(row => row.source === site);
    }, [sourcesWeekdayData, site]);
    const keywordFiltered = React.useMemo(() => {
        const rows = ((keywordStats || []) as ChartDataset).filter(row => keywordAllowedSet.has(String(row.site ?? '')));
        return site === ALL_SITES ? rows : rows.filter(row => String(row.site ?? '') === site);
    }, [keywordStats, site]);

    const { processedData: sourcesDateWide, keys: sourcesDateKeys } = React.useMemo(
        () => processChartData(sourcesDateFiltered as unknown as SourceDateStat[], 'dateCreated', 'source', 'total'),
        [sourcesDateFiltered]
    );
    const { processedData: sourcesHourWide, keys: sourcesHourKeys } = React.useMemo(
        () => processChartData(sourcesHourFiltered as unknown as SourceHourStat[], 'hour', 'source', 'total'),
        [sourcesHourFiltered]
    );
    const { processedData: sourcesWeekdayWide, keys: sourcesWeekdayKeys } = React.useMemo(
        () => processChartData(sourcesWeekdayFiltered as unknown as SourceWeekdayStat[], 'weekday', 'source', 'total'),
        [sourcesWeekdayFiltered]
    );

    const allSources = React.useMemo(() => {
        const set = new Set([...sourcesDateKeys, ...sourcesHourKeys, ...sourcesWeekdayKeys]);
        return Array.from(set);
    }, [sourcesDateKeys, sourcesHourKeys, sourcesWeekdayKeys]);

    return {
        timeRange,
        setTimeRange,
        includeOldJobs,
        setIncludeOldJobs,
        site,
        setSite,
        historyData,
        sourcesDateWide,
        sourcesDateKeys,
        sourcesHourWide,
        sourcesHourKeys,
        sourcesWeekdayWide,
        sourcesWeekdayKeys,
        filterConfigData,
        keywordStats: keywordFiltered,
        allSources
    };
};
