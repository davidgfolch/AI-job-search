import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday, getFilterConfigStats } from './api/StatisticsApi';
import { processChartData, getDateRange } from './utils/chartUtils';

export const useStatistics = () => {
    const [timeRange, setTimeRange] = React.useState('Last 3 months');
    const [includeOldJobs, setIncludeOldJobs] = React.useState(true);

    const { startDate, endDate } = React.useMemo(() => getDateRange(timeRange), [timeRange]);

    const { data: historyData } = useQuery({ queryKey: ['statistics', 'history', startDate, endDate, includeOldJobs], queryFn: () => getHistoryStats(startDate, endDate, includeOldJobs) });
    const { data: sourcesDateData } = useQuery({ queryKey: ['statistics', 'sourcesDate', startDate, endDate, includeOldJobs], queryFn: () => getSourcesByDate(startDate, endDate, includeOldJobs) });
    const { data: sourcesHourData } = useQuery({ queryKey: ['statistics', 'sourcesHour', startDate, endDate, includeOldJobs], queryFn: () => getSourcesByHour(startDate, endDate, includeOldJobs) });
    const { data: sourcesWeekdayData } = useQuery({ queryKey: ['statistics', 'sourcesWeekday', startDate, endDate, includeOldJobs], queryFn: () => getSourcesByWeekday(startDate, endDate, includeOldJobs) });
    const { data: filterConfigData } = useQuery({ queryKey: ['statistics', 'filterConfigs', startDate, endDate, includeOldJobs], queryFn: () => getFilterConfigStats(startDate, endDate, includeOldJobs) });
    
    // Process data to unify sources and handle colors
    const { processedData: sourcesDateWide, keys: sourcesDateKeys } = React.useMemo(
        () => processChartData(sourcesDateData || [], 'dateCreated', 'source', 'total'), 
        [sourcesDateData]
    );

    const { processedData: sourcesHourWide, keys: sourcesHourKeys } = React.useMemo(
        () => processChartData(sourcesHourData || [], 'hour', 'source', 'total'), 
        [sourcesHourData]
    );

    const { processedData: sourcesWeekdayWide, keys: sourcesWeekdayKeys } = React.useMemo(
        () => processChartData(sourcesWeekdayData || [], 'weekday', 'source', 'total'), 
        [sourcesWeekdayData]
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
        historyData,
        sourcesDateWide,
        sourcesDateKeys,
        sourcesHourWide,
        sourcesHourKeys,
        sourcesWeekdayWide,
        sourcesWeekdayKeys,
        filterConfigData,
        allSources
    };
};
