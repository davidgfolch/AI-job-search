import React from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    BarChart, Bar
} from 'recharts';
import CustomTooltip from '../components/CustomTooltip';
import { getColorForSource } from './chartUtils';

export const renderWeekdayChart = (data: any[], sourcesWeekdayKeys: string[], allSources: string[]) => (
    <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
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
);

export const renderDateChart = (data: any[], sourcesDateKeys: string[], allSources: string[]) => (
    <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
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
);

export const renderHourChart = (data: any[], sourcesHourKeys: string[], allSources: string[]) => (
    <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
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
);

export const renderFilterConfigChart = (data: any[]) => (
    <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data || []}>
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
);

export const renderHistoryChart = (data: any[]) => (
    <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
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
);