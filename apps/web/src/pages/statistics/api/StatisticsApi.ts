import axios from 'axios';

const API_Base = 'http://localhost:8000/api/statistics';

export interface HistoryStat {
    dateCreated: string;
    applied: number;
    discarded: number;
    interview: number;
    discarded_cumulative: number;
    interview_cumulative: number;
}

export interface SourceDateStat {
    dateCreated: string;
    total: number;
    source: string;
}

export interface SourceHourStat {
    hour: number;
    total: number;
    source: string;
}

export const getHistoryStats = async (): Promise<HistoryStat[]> => {
    const response = await axios.get(`${API_Base}/history`);
    return response.data;
};

export const getSourcesByDate = async (): Promise<SourceDateStat[]> => {
    const response = await axios.get(`${API_Base}/sources-date`);
    return response.data;
};

export const getSourcesByHour = async (): Promise<SourceHourStat[]> => {
    const response = await axios.get(`${API_Base}/sources-hour`);
    return response.data;
};

export interface SourceWeekdayStat {
    weekday: number;
    total: number;
    source: string;
}

export const getSourcesByWeekday = async (): Promise<SourceWeekdayStat[]> => {
    const response = await axios.get(`${API_Base}/sources-weekday`);
    return response.data;
};

export interface FilterConfigStat {
    name: string;
    count: number;
}

export const getFilterConfigStats = async (): Promise<FilterConfigStat[]> => {
    const response = await axios.get(`${API_Base}/filter-configs`);
    return response.data;
};
