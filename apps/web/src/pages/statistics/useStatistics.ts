import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday, getFilterConfigStats } from './api/StatisticsApi';
import { processChartData } from './utils/chartUtils';

export const useStatistics = () => {
    const [timeRange, setTimeRange] = React.useState('All');
    const [includeOldJobs, setIncludeOldJobs] = React.useState(true);

    const { startDate, endDate } = React.useMemo(() => {
        if (timeRange === 'All') return { startDate: undefined, endDate: undefined };
        const end = new Date();
        const start = new Date();
        if (timeRange === 'Last year') {
            start.setFullYear(start.getFullYear() - 1);
        } else if (timeRange === 'Last 6 months') {
            start.setMonth(start.getMonth() - 6);
        } else if (timeRange === 'Last month') {
            start.setMonth(start.getMonth() - 1);
        } else if (timeRange === 'Last week') {
            start.setDate(start.getDate() - 7);
        } else if (timeRange === 'Last day') {
            start.setDate(start.getDate() - 1);
        }
        return { startDate: start.toISOString().split('T')[0], endDate: end.toISOString().split('T')[0] };
    }, [timeRange]);

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
