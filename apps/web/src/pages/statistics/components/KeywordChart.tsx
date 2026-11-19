import React from 'react';
import {
    ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import type { ChartDataset } from '../utils/chartUtils';
import { buildKeywordChartData, keywordRowsWithDuplicates } from '../utils/keywordChartUtils';

interface KeywordChartProps {
    rows: ChartDataset;
}

const shortDate = (value: unknown) => String(value ?? '').slice(5);

const KeywordChart: React.FC<KeywordChartProps> = ({ rows }) => {
    const { data, series } = React.useMemo(() => buildKeywordChartData(rows), [rows]);
    const duplicates = React.useMemo(() => keywordRowsWithDuplicates(rows), [rows]);

    if (!data.length) return <div className="keyword-empty">No keyword search data in this date range.</div>;

    return (
        <div className="keyword-chart">
            <div className="keyword-chart-canvas">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={shortDate} interval="preserveStartEnd" minTickGap={24} angle={-35} textAnchor="end" height={50} />
                        <YAxis allowDecimals={false} />
                        <Tooltip labelFormatter={(label) => String(label)} />
                        <Legend />
                        {series.map(item => (
                            <React.Fragment key={item.key}>
                                <Bar dataKey={item.newKey} stackId="keywords" fill={item.color} name={item.label} />
                                <Bar dataKey={item.duplicateKey} stackId="keywords" fill={item.color} fillOpacity={0.35} stroke={item.color} name={`${item.label} (duplicates)`} legendType="none" />
                                <Line type="monotone" dataKey={item.totalKey} stroke={item.color} strokeDasharray="5 5" dot={false} name={`${item.label} (reported)`} legendType="none" />
                            </React.Fragment>
                        ))}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
            <div className="keyword-duplicates">
                <h3>Already-in-DB duplicates by keyword</h3>
                {duplicates.length ? (
                    <table className="keyword-duplicates-table">
                        <thead><tr><th>Date</th><th>Site</th><th>Keyword</th><th>Duplicates</th><th>Duplicate ids</th></tr></thead>
                        <tbody>
                            {duplicates.map(row => (
                                <tr key={`${row.date}|${row.site}|${row.keyword}`}>
                                    <td>{row.date}</td><td>{row.site}</td><td>{row.keyword}</td>
                                    <td>{row.duplicates}</td><td>{row.duplicate_ids || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : <p className="keyword-empty">No already-in-DB duplicates logged in this date range.</p>}
            </div>
        </div>
    );
};

export default KeywordChart;
