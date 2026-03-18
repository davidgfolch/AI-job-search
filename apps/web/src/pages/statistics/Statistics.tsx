import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import ChartCard from './components/ChartCard';
import CustomTooltip from './components/CustomTooltip';
import StatisticsControls from './components/StatisticsControls';
import { getColorForSource } from './utils/chartUtils';
import './Statistics.css';
import { useStatistics } from './useStatistics';
import PageHeader from '../common/components/PageHeader';

const Statistics = () => {
    const [columns, setColumns] = React.useState(3);
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
                    <ChartCard title="Job Postings by Source & Day of Week">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={sourcesWeekdayWide}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="weekday" 
                                    tickFormatter={(tick) => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][tick - 1] || tick}
                                />
                                <YAxis />
                                <RechartsTooltip content={<CustomTooltip showDateLabel={false} />} />
                                <Legend />
                                {sourcesWeekdayKeys.map((key) => (
                                    <Bar key={key} dataKey={key} stackId="a" fill={getColorForSource(key, allSources)} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    <ChartCard title="Job Postings by Source & Created Date">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={sourcesDateWide}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="dateCreated" 
                                    angle={-45}
                                    textAnchor="end"
                                    height={80}
                                />
                                <YAxis />
                                <RechartsTooltip content={<CustomTooltip />} />
                                <Legend />
                                {sourcesDateKeys.map((key) => (
                                    <Bar key={key} dataKey={key} stackId="a" fill={getColorForSource(key, allSources)} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    <ChartCard title="Job Postings by Source & Day Time">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={sourcesHourWide}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="hour" />
                                <YAxis />
                                <RechartsTooltip content={<CustomTooltip showDateLabel={false} />} />
                                <Legend />
                                {sourcesHourKeys.map((key) => (
                                    <Bar key={key} dataKey={key} stackId="a" fill={getColorForSource(key, allSources)} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    <ChartCard title="Filter Configurations & Job Counts">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={filterConfigData || []}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="name" 
                                    angle={-45}
                                    textAnchor="end"
                                    height={100}
                                />
                                <YAxis />
                                <RechartsTooltip />
                                <Bar dataKey="count" fill="#8884d8" name="Job Count" />
                            </BarChart>
                        </ResponsiveContainer>
                    </ChartCard>

                    <ChartCard title="Applied vs Discarded Jobs (History)">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={historyData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="dateCreated" />
                                <YAxis />
                                <RechartsTooltip content={<CustomTooltip showDateLabel={true} />} />
                                <Legend />
                                <Line type="monotone" dataKey="applied" stroke="#0000ff" name="Applied" />
                                <Line type="monotone" dataKey="discarded" stroke="#ff0000" name="Discarded" />
                                <Line type="monotone" dataKey="interview" stroke="#00ff00" name="Interview" />
                                <Line type="monotone" dataKey="discarded_cumulative" stroke="#ff0000" strokeDasharray="5 5" name="Discarded (Σ)" />
                                <Line type="monotone" dataKey="interview_cumulative" stroke="#00ff00" strokeDasharray="5 5" name="Interview (Σ)" />
                            </LineChart>
                        </ResponsiveContainer>
                    </ChartCard>

                </div>
            </main>
        </div>
    );
};

export default Statistics;
