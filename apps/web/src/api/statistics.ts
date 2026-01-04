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
