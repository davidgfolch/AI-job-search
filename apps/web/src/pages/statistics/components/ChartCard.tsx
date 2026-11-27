import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday, getFilterConfigStats, getKeywordStats
} from '../api/StatisticsApi';
import type { HistoryStat, SourceDateStat, SourceHourStat, SourceWeekdayStat, FilterConfigStat, KeywordStat } from '../api/StatisticsApi';
import { processChartData, getDateRange, type ChartDataset } from '../utils/chartUtils';
import StatisticsFilters from './StatisticsFilters';
import { ALL_SITES, KEYWORD_SITES, SCRAPER_SITES } from '../sites';

type ChartData = HistoryStat[] | SourceDateStat[] | SourceHourStat[] | SourceWeekdayStat[] | FilterConfigStat[] | KeywordStat[];

interface ChartCardProps {
    title: string;
    children: React.ReactNode | ((data: ChartDataset | null) => React.ReactNode);
    chartType: 'weekday' | 'date' | 'hour' | 'filterConfig' | 'history' | 'keyword';
    parentTimeRange: string;
    parentIncludeOldJobs: boolean;
    site?: string;
    onExpandChange: (chartTitle: string | null) => void;
    onFilterChange: (timeRange: string, includeOldJobs: boolean) => void;
    expandedChart: string | null;
}

const allowed = new Set(SCRAPER_SITES);
const keywordAllowed = new Set(KEYWORD_SITES);

const ChartCard: React.FC<ChartCardProps> = ({
    title, children, chartType, parentTimeRange, parentIncludeOldJobs, site = ALL_SITES, onExpandChange, onFilterChange, expandedChart
}) => {
    const [localTimeRange, setLocalTimeRange] = useState(parentTimeRange);
    const [localIncludeOldJobs, setLocalIncludeOldJobs] = useState(parentIncludeOldJobs);
    const [syncedFilters, setSyncedFilters] = useState({ timeRange: parentTimeRange, includeOldJobs: parentIncludeOldJobs });
    if (syncedFilters.timeRange !== parentTimeRange || syncedFilters.includeOldJobs !== parentIncludeOldJobs) {
        setSyncedFilters({ timeRange: parentTimeRange, includeOldJobs: parentIncludeOldJobs });
        setLocalTimeRange(parentTimeRange);
        setLocalIncludeOldJobs(parentIncludeOldJobs);
    }

    const isThisChartExpanded = expandedChart === title;
    // We only fetch if the user changes filters in the expanded view
    const hasLocalFiltersChanged = localTimeRange !== parentTimeRange || localIncludeOldJobs !== parentIncludeOldJobs;

    const { startDate, endDate } = React.useMemo(() => getDateRange(localTimeRange), [localTimeRange]);

    const fetchData = useCallback(() => {
        switch (chartType) {
            case 'history': return getHistoryStats(startDate, endDate, localIncludeOldJobs);
            case 'date': return getSourcesByDate(startDate, endDate, localIncludeOldJobs);
            case 'hour': return getSourcesByHour(startDate, endDate, localIncludeOldJobs);
            case 'weekday': return getSourcesByWeekday(startDate, endDate, localIncludeOldJobs);
            case 'filterConfig': return getFilterConfigStats(startDate, endDate);
            case 'keyword': return getKeywordStats(startDate, endDate);
        }
    }, [chartType, startDate, endDate, localIncludeOldJobs]);

    const usesSite = chartType === 'date' || chartType === 'hour' || chartType === 'weekday' || chartType === 'keyword';
    const { data: rawData, isFetching } = useQuery<ChartData>({
        // The filter-configs and keyword endpoints do not take includeOldJobs, so it is not part of the cache key.
        queryKey: chartType === 'filterConfig' || chartType === 'history'
            ? (chartType === 'history' ? ['statistics', chartType, startDate, endDate, localIncludeOldJobs] : ['statistics', chartType, startDate, endDate])
            : ['statistics', chartType, startDate, endDate, localIncludeOldJobs, site],
        queryFn: fetchData,
        enabled: isThisChartExpanded && (hasLocalFiltersChanged || usesSite)
    });

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isThisChartExpanded) {
                onExpandChange(null);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isThisChartExpanded, onExpandChange]);

    const handleClose = () => {
        onFilterChange(localTimeRange, localIncludeOldJobs);
        onExpandChange(null);
    };

    const handleTimeRangeChange = (value: string) => {
        setLocalTimeRange(value);
    };

    const handleIncludeOldJobsChange = (checked: boolean) => {
        setLocalIncludeOldJobs(checked);
    };

    const getProcessedData = () => {
        if (!rawData) return null;
        switch (chartType) {
            case 'date': {
                const rows = ((rawData as SourceDateStat[]) || []).filter(r => allowed.has(r.source) && (site === ALL_SITES || r.source === site));
                const { processedData } = processChartData(rows, 'dateCreated', 'source', 'total');
                return processedData;
            }
            case 'hour': {
                const rows = ((rawData as SourceHourStat[]) || []).filter(r => allowed.has(r.source) && (site === ALL_SITES || r.source === site));
                const { processedData } = processChartData(rows, 'hour', 'source', 'total');
                return processedData;
            }
            case 'weekday': {
                const rows = ((rawData as SourceWeekdayStat[]) || []).filter(r => allowed.has(r.source) && (site === ALL_SITES || r.source === site));
                const { processedData } = processChartData(rows, 'weekday', 'source', 'total');
                return processedData;
            }
            case 'keyword': {
                const rows = ((rawData as KeywordStat[]) || []).filter(r => keywordAllowed.has(String(r.site ?? '')));
                return site === ALL_SITES ? rows : rows.filter(r => String(r.site ?? '') === site);
            }
            default:
                return rawData;
        }
    };

    const processedData = getProcessedData();

    return (
        <section className={`chart-section ${isThisChartExpanded ? 'expanded' : ''}`}>
            <div className="chart-header">
                <h2>{title}</h2>
                <button
                    className="expand-btn"
                    onClick={() => isThisChartExpanded ? handleClose() : onExpandChange(title)}
                    title={isThisChartExpanded ? "Close Full Screen" : "Expand to Full Screen"}
                >
                    {isThisChartExpanded ? (
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <polyline points="9 21 3 21 3 15"></polyline>
                            <line x1="21" y1="3" x2="14" y2="10"></line>
                            <line x1="3" y1="21" x2="10" y2="14"></line>
                        </svg>
                    )}
                </button>
            </div>
            {isThisChartExpanded && (
                <div className="fullscreen-controls">
                    <StatisticsFilters
                        timeRange={localTimeRange}
                        onTimeRangeChange={handleTimeRangeChange}
                        includeOldJobs={localIncludeOldJobs}
                        onIncludeOldJobsChange={handleIncludeOldJobsChange}
                    />
                </div>
            )}
            <div className="chart-container">
                {isThisChartExpanded && isFetching ? (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                        Loading...
                    </div>
                ) : isThisChartExpanded && processedData ? (
                    typeof children === 'function' ? children(processedData) : children
                ) : (
                    typeof children === 'function' ? children(null) : children
                )}
            </div>
        </section>
    );
};

export default ChartCard;