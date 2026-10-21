import apiClient from '../../common/api/ApiClient';

const API_Base = '/statistics';

export type HistoryStat = {
    dateCreated: string;
    applied: number;
    discarded: number;
    interview: number;
    discarded_cumulative: number;
    interview_cumulative: number;
};

export type SourceDateStat = {
    dateCreated: string;
    total: number;
    source: string;
};

export type SourceHourStat = {
    hour: number;
    total: number;
    source: string;
};

export type SourceWeekdayStat = {
    weekday: number;
    total: number;
    source: string;
};

export type FilterConfigStat = {
    name: string;
    count: number;
};

const buildDateParams = (startDate?: string, endDate?: string, includeOldJobs?: boolean) => ({
    ...(startDate && { start_date: startDate }),
    ...(endDate && { end_date: endDate }),
    ...(typeof includeOldJobs === 'boolean' && { include_old_jobs: includeOldJobs }),
});

export const getHistoryStats = async (startDate?: string, endDate?: string, includeOldJobs?: boolean): Promise<HistoryStat[]> => {
    const response = await apiClient.get(`${API_Base}/history`, { params: buildDateParams(startDate, endDate, includeOldJobs) });
    return response.data;
};

export const getSourcesByDate = async (startDate?: string, endDate?: string, includeOldJobs?: boolean): Promise<SourceDateStat[]> => {
    const response = await apiClient.get(`${API_Base}/sources-date`, { params: buildDateParams(startDate, endDate, includeOldJobs) });
    return response.data;
};

export const getSourcesByHour = async (startDate?: string, endDate?: string, includeOldJobs?: boolean): Promise<SourceHourStat[]> => {
    const response = await apiClient.get(`${API_Base}/sources-hour`, { params: buildDateParams(startDate, endDate, includeOldJobs) });
    return response.data;
};

export const getSourcesByWeekday = async (startDate?: string, endDate?: string, includeOldJobs?: boolean): Promise<SourceWeekdayStat[]> => {
    const response = await apiClient.get(`${API_Base}/sources-weekday`, { params: buildDateParams(startDate, endDate, includeOldJobs) });
    return response.data;
};

export const getFilterConfigStats = async (startDate?: string, endDate?: string): Promise<FilterConfigStat[]> => {
    const response = await apiClient.get(`${API_Base}/filter-configs`, { params: buildDateParams(startDate, endDate) });
    return response.data;
};
