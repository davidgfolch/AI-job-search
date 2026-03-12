import apiClient from '../../common/api/ApiClient';

const API_Base = '/statistics';

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

export interface SourceWeekdayStat {
    weekday: number;
    total: number;
    source: string;
}

export interface FilterConfigStat {
    name: string;
    count: number;
}

const buildDateParams = (startDate?: string, endDate?: string) => ({
    ...(startDate && { start_date: startDate }),
    ...(endDate && { end_date: endDate }),
});

export const getHistoryStats = async (startDate?: string, endDate?: string): Promise<HistoryStat[]> => {
    const response = await apiClient.get(`${API_Base}/history`, { params: buildDateParams(startDate, endDate) });
    return response.data;
};

export const getSourcesByDate = async (startDate?: string, endDate?: string): Promise<SourceDateStat[]> => {
    const response = await apiClient.get(`${API_Base}/sources-date`, { params: buildDateParams(startDate, endDate) });
    return response.data;
};

export const getSourcesByHour = async (startDate?: string, endDate?: string): Promise<SourceHourStat[]> => {
    const response = await apiClient.get(`${API_Base}/sources-hour`, { params: buildDateParams(startDate, endDate) });
    return response.data;
};

export const getSourcesByWeekday = async (startDate?: string, endDate?: string): Promise<SourceWeekdayStat[]> => {
    const response = await apiClient.get(`${API_Base}/sources-weekday`, { params: buildDateParams(startDate, endDate) });
    return response.data;
};

export const getFilterConfigStats = async (startDate?: string, endDate?: string): Promise<FilterConfigStat[]> => {
    const response = await apiClient.get(`${API_Base}/filter-configs`, { params: buildDateParams(startDate, endDate) });
    return response.data;
};
