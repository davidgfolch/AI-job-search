import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import type { ChartDataset } from '../utils/chartUtils';
import { buildKeywordChartData } from '../utils/keywordChartUtils';

interface KeywordChartProps {
    rows: ChartDataset;
}

const shortDate = (value: unknown) => String(value ?? '').slice(5);

const KeywordChart: React.FC<KeywordChartProps> = ({ rows }) => {
    const { data, series } = React.useMemo(() => buildKeywordChartData(rows), [rows]);

    if (!data.length) return <div className="keyword-empty">No keyword search data in this date range.</div>;

    return (
        <div className="keyword-chart">
            <div className="keyword-chart-canvas">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" tickFormatter={shortDate} interval="preserveStartEnd" minTickGap={24} angle={-35} textAnchor="end" height={50} />
                        <YAxis allowDecimals={false} />
                        <Tooltip labelFormatter={(label) => String(label)} />
                        <Legend />
                        {series.map(item => (
                            <Line key={item.key} type="monotone" dataKey={item.newKey} stroke={item.color} dot={false} name={item.label} />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default KeywordChart;
