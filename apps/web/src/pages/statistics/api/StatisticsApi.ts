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

export const getHistoryStats = async (startDate?: string, endDate?: string): Promise<HistoryStat[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await axios.get(`${API_Base}/history`, { params });
    return response.data;
};

export const getSourcesByDate = async (startDate?: string, endDate?: string): Promise<SourceDateStat[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await axios.get(`${API_Base}/sources-date`, { params });
    return response.data;
};

export const getSourcesByHour = async (startDate?: string, endDate?: string): Promise<SourceHourStat[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await axios.get(`${API_Base}/sources-hour`, { params });
    return response.data;
};

export interface SourceWeekdayStat {
    weekday: number;
    total: number;
    source: string;
}

export const getSourcesByWeekday = async (startDate?: string, endDate?: string): Promise<SourceWeekdayStat[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await axios.get(`${API_Base}/sources-weekday`, { params });
    return response.data;
};

export interface FilterConfigStat {
    name: string;
    count: number;
}

export const getFilterConfigStats = async (startDate?: string, endDate?: string): Promise<FilterConfigStat[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await axios.get(`${API_Base}/filter-configs`, { params });
    return response.data;
};
