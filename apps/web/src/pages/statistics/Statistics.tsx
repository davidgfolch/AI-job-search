import React, { useState, useRef } from 'react';
import ChartCard from './components/ChartCard';
import StatisticsControls from './components/StatisticsControls';
import {
    renderWeekdayChart, renderDateChart, renderHourChart, renderFilterConfigChart, renderHistoryChart
} from './utils/statisticsChartRenderers';
import './Statistics.css';
import { useStatistics } from './useStatistics';
import PageHeader from '../common/components/PageHeader';

const Statistics = () => {
    const [columns, setColumns] = useState(3);
    const [expandedChart, setExpandedChart] = useState<string | null>(null);
    const [fullScreenFilters, setFullScreenFilters] = useState<{ timeRange: string; includeOldJobs: boolean } | null>(null);
    const prevFiltersRef = useRef<{ timeRange: string; includeOldJobs: boolean }>({ timeRange: '', includeOldJobs: false });

    const {
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
    } = useStatistics();

    React.useEffect(() => {
        prevFiltersRef.current = { timeRange, includeOldJobs };
    }, [timeRange, includeOldJobs]);

    const handleExpandChange = (chartTitle: string | null) => {
        if (chartTitle) {
            prevFiltersRef.current = { timeRange, includeOldJobs };
            setExpandedChart(chartTitle);
        } else {
            const prevFilters = prevFiltersRef.current;
            const filterChanged = fullScreenFilters &&
                (fullScreenFilters.timeRange !== prevFilters.timeRange ||
                 fullScreenFilters.includeOldJobs !== prevFilters.includeOldJobs);

            if (filterChanged) {
                setTimeRange(fullScreenFilters.timeRange);
                setIncludeOldJobs(fullScreenFilters.includeOldJobs);
            }
            setExpandedChart(null);
            setFullScreenFilters(null);
        }
    };

    const handleFilterChange = (newTimeRange: string, newIncludeOldJobs: boolean) => {
        setFullScreenFilters({ timeRange: newTimeRange, includeOldJobs: newIncludeOldJobs });
    };

    return (
        <div className="statistics-page">
            <PageHeader title="Statistics" />
            <StatisticsControls
                timeRange={timeRange}
                setTimeRange={setTimeRange}
                includeOldJobs={includeOldJobs}
                setIncludeOldJobs={setIncludeOldJobs}
                columns={columns}
                setColumns={setColumns}
            />
            <main className="statistics-content">
                <div className="charts-grid" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` } as React.CSSProperties}>
                    <ChartCard
                        title="Job Postings by Source & Day of Week"
                        chartType="weekday"
                        parentTimeRange={timeRange}
                        parentIncludeOldJobs={includeOldJobs}
                        onExpandChange={handleExpandChange}
                        onFilterChange={handleFilterChange}
                        expandedChart={expandedChart}
                    >
                        {(data: any) => renderWeekdayChart(data || sourcesWeekdayWide, sourcesWeekdayKeys, allSources)}
                    </ChartCard>

                    <ChartCard
                        title="Job Postings by Source & Created Date"
                        chartType="date"
                        parentTimeRange={timeRange}
                        parentIncludeOldJobs={includeOldJobs}
                        onExpandChange={handleExpandChange}
                        onFilterChange={handleFilterChange}
                        expandedChart={expandedChart}
                    >
                        {(data: any) => renderDateChart(data || sourcesDateWide, sourcesDateKeys, allSources)}
                    </ChartCard>

                    <ChartCard
                        title="Job Postings by Source & Day Time"
                        chartType="hour"
                        parentTimeRange={timeRange}
                        parentIncludeOldJobs={includeOldJobs}
                        onExpandChange={handleExpandChange}
                        onFilterChange={handleFilterChange}
                        expandedChart={expandedChart}
                    >
                        {(data: any) => renderHourChart(data || sourcesHourWide, sourcesHourKeys, allSources)}
                    </ChartCard>

                    <ChartCard
                        title="Filter Configurations & Job Counts"
                        chartType="filterConfig"
                        parentTimeRange={timeRange}
                        parentIncludeOldJobs={includeOldJobs}
                        onExpandChange={handleExpandChange}
                        onFilterChange={handleFilterChange}
                        expandedChart={expandedChart}
                    >
                        {(data: any) => renderFilterConfigChart(data || filterConfigData || [])}
                    </ChartCard>

                    <ChartCard
                        title="Applied vs Discarded Jobs (History)"
                        chartType="history"
                        parentTimeRange={timeRange}
                        parentIncludeOldJobs={includeOldJobs}
                        onExpandChange={handleExpandChange}
                        onFilterChange={handleFilterChange}
                        expandedChart={expandedChart}
                    >
                        {(data: any) => renderHistoryChart(data || historyData)}
                    </ChartCard>

                </div>
            </main>
        </div>
    );
};

export default Statistics;