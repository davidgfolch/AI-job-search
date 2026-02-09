import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import ChartCard from './components/ChartCard';
import { getColorForSource } from './utils/chartUtils';
import './Statistics.css';
import { useStatistics } from './useStatistics';

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="custom-tooltip" style={{ backgroundColor: 'white', padding: '10px', border: '1px solid #ccc' }}>
                <p className="label">{`${label}`}</p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} style={{ color: entry.color }}>
                        {entry.name}: {entry.value}
                        {entry.name === 'Other' && entry.payload.otherDetails && (
                            <div style={{ fontSize: '0.8em', marginLeft: '10px', color: '#666' }}>
                                {Object.entries(entry.payload.otherDetails).map(([source, count]) => (
                                    <div key={source}>{source}: {count as number}</div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

const Statistics = () => {
    const [columns, setColumns] = React.useState(3);
    const {
        timeRange,
        setTimeRange,
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
            <header className="app-header">
                <div className="header-content">
                    <h1>AI Job Search Statistics</h1>
                    <div className="layout-controls">
                        <span className="layout-label">Date Range:</span>
                        <select 
                            className="date-range-select"
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                            style={{ marginRight: '20px', padding: '5px', borderRadius: '4px', border: '1px solid #ccc' }}
                        >
                            <option value="All">All</option>
                            <option value="Last year">Last year</option>
                            <option value="Last 6 months">Last 6 months</option>
                            <option value="Last month">Last month</option>
                        </select>

                        <span className="layout-label">Layout:</span>
                        <div className="layout-buttons">
                            <button 
                                className={`layout-btn ${columns === 1 ? 'active' : ''}`}
                                onClick={() => setColumns(1)}
                                title="Single Column"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                </svg>
                            </button>
                            <button 
                                className={`layout-btn ${columns === 2 ? 'active' : ''}`}
                                onClick={() => setColumns(2)}
                                title="Two Columns"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                    <line x1="12" y1="3" x2="12" y2="21"></line>
                                </svg>
                            </button>
                            <button 
                                className={`layout-btn ${columns === 3 ? 'active' : ''}`}
                                onClick={() => setColumns(3)}
                                title="Three Columns"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                    <line x1="9" y1="3" x2="9" y2="21"></line>
                                    <line x1="15" y1="3" x2="15" y2="21"></line>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </header>
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
                                <RechartsTooltip content={<CustomTooltip />} />
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
                                <XAxis dataKey="dateCreated" />
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
                                <RechartsTooltip content={<CustomTooltip />} />
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
                                <RechartsTooltip />
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
