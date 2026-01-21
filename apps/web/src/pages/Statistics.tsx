import { useQuery } from '@tanstack/react-query';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import { getHistoryStats, getSourcesByDate, getSourcesByHour, getSourcesByWeekday } from '../api/statistics';
import './Statistics.css';

const Statistics = () => {
    const { data: historyData } = useQuery({ queryKey: ['statistics', 'history'], queryFn: getHistoryStats });
    const { data: sourcesDateData } = useQuery({ queryKey: ['statistics', 'sourcesDate'], queryFn: getSourcesByDate });
    const { data: sourcesHourData } = useQuery({ queryKey: ['statistics', 'sourcesHour'], queryFn: getSourcesByHour });
    const { data: sourcesWeekdayData } = useQuery({ queryKey: ['statistics', 'sourcesWeekday'], queryFn: getSourcesByWeekday });

    // Transform data for stacked bars if needed, or rely on Recharts grouping
    // For "Sources by Date" and "Sources by Hour", the data is flat "long" format (source column).
    // Recharts expects "wide" format for stacked/grouped bars typically (one row per x-axis value, keys for series).
    // We need to pivot the data.

    const pivotData = (data: any[], xKey: string, seriesKey: string, valueKey: string) => {
        if (!data) return [];
        const result: any[] = [];
        const map = new Map<string, any>();
        
        data.forEach(item => {
            const xVal = item[xKey];
            if (!map.has(xVal)) {
                map.set(xVal, { [xKey]: xVal });
                result.push(map.get(xVal));
            }
            map.get(xVal)[item[seriesKey]] = item[valueKey];
        });
        return result.sort((a, b) => (a[xKey] > b[xKey] ? 1 : -1));
    };

    const sourcesDateWide = pivotData(sourcesDateData || [], 'dateCreated', 'source', 'total');
    const sourcesHourWide = pivotData(sourcesHourData || [], 'hour', 'source', 'total');
    const sourcesWeekdayWide = pivotData(sourcesWeekdayData || [], 'weekday', 'source', 'total');

    // Get unique sources for colors/keys
    const getSources = (data: any[]) => {
      if (!data) return [];
      const sources = new Set<string>();
      data.forEach(item => {
        Object.keys(item).forEach(key => {
          if (key !== 'dateCreated' && key !== 'hour' && key !== 'weekday') sources.add(key);
        });
      });
      return Array.from(sources);
    }

    const sourcesDateKeys = getSources(sourcesDateWide);
    const sourcesHourKeys = getSources(sourcesHourWide);
    const sourcesWeekdayKeys = getSources(sourcesWeekdayWide);
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00C49F'];

    return (
        <div className="statistics-page">
            <header className="app-header">
                <h1>AI Job Search Statistics</h1>
            </header>
            <main className="statistics-content">
                <section className="chart-section">
                    <h2>Applied vs Discarded Jobs (History)</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={400}>
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
                    </div>
                </section>

                <section className="chart-section">
                    <h2>Job Postings by Source & Created Date</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={400}>
                            <BarChart data={sourcesDateWide}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="dateCreated" />
                                <YAxis />
                                <RechartsTooltip />
                                <Legend />
                                {sourcesDateKeys.map((key, index) => (
                                    <Bar key={key} dataKey={key} stackId="a" fill={colors[index % colors.length]} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                <section className="chart-section">
                    <h2>Job Postings by Source & Day Time</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={400}>
                            <BarChart data={sourcesHourWide}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="hour" />
                                <YAxis />
                                <RechartsTooltip />
                                <Legend />
                                {sourcesHourKeys.map((key, index) => (
                                    <Bar key={key} dataKey={key} stackId="a" fill={colors[index % colors.length]} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>

                <section className="chart-section">
                    <h2>Job Postings by Source & Day of Week</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={400}>
                            <BarChart data={sourcesWeekdayWide}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="weekday" 
                                    tickFormatter={(tick) => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][tick - 1] || tick}
                                />
                                <YAxis />
                                <RechartsTooltip />
                                <Legend />
                                {sourcesWeekdayKeys.map((key, index) => (
                                    <Bar key={key} dataKey={key} stackId="a" fill={colors[index % colors.length]} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </section>
            </main>
        </div>
    );
};

export default Statistics;
