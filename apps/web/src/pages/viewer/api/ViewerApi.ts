import apiClient from '../../common/api/ApiClient';
import type {
  AppliedCompanyJob, Job, JobListParams, JobListResponse, SalaryHistoryEntry, WatcherStats,
} from './ViewerApiTypes';

export * from './ViewerApiTypes';

const handleRequest = async <T>(request: Promise<{ data: T }>, errorMessage: string): Promise<T> => {
  try {
    const response = await request;
    return response.data;
  } catch (error) {
    throw new Error(`${errorMessage}: ${error instanceof Error ? error.message : String(error)}`);
  }
};

let timezonePromise: Promise<{ offset_minutes: number }> | null = null;

export const jobsApi = {
  getJobs: async (params: JobListParams = {}): Promise<JobListResponse> => {
    return handleRequest(apiClient.get<JobListResponse>('/jobs', { params }),
      'Error loading jobs');
  },



  getWatcherStats: async (cutoffMap: Record<number, string>): Promise<Record<number, WatcherStats>> => {
    const params: Record<string, string> = { 
      config_ids: Object.keys(cutoffMap).join(',')
    };
    Object.entries(cutoffMap).forEach(([id, cutoff]) => {
      params[`from_${id}`] = cutoff;
    });
    return handleRequest(apiClient.get<Record<number, WatcherStats>>('/jobs/watcher-stats', { params }),
      'Error getting watcher stats');
  },

  createJob: async (data: Partial<Job>): Promise<Job> => {
    return handleRequest(apiClient.post<Job>('/jobs', data),
      'Error creating job');
  },

  getJob: async (id: number): Promise<Job> => {
    return handleRequest(apiClient.get<Job>(`/jobs/${id}`),
      'Error loading job details');
  },

  updateJob: async (id: number, data: Partial<Job>): Promise<Job> => {
    return handleRequest(apiClient.patch<Job>(`/jobs/${id}`, data),
      'Error updating job');
  },


  getAppliedJobsByCompany: async (company: string, client?: string): Promise<AppliedCompanyJob[]> => {
    const params: Record<string, string> = { company };
    if (client) {
      params.client = client;
    }
    return handleRequest(apiClient.get<AppliedCompanyJob[]>('/jobs/applied-by-company', { params }),
      'Error loading applied jobs');
  },

  bulkUpdateJobs: async (payload: {
    ids?: number[];
    filters?: JobListParams;
    update: Partial<Job>;
    select_all?: boolean;
  }): Promise<{ updated: number }> => {
    return handleRequest(apiClient.post<{ updated: number }>('/jobs/bulk', payload),
      'Error updating jobs');
  },

  deleteJobs: async (payload: {
    ids?: number[];
    filters?: JobListParams;
    select_all?: boolean;
  }): Promise<{ deleted: number }> => {
    return handleRequest(apiClient.post<{ deleted: number }>('/jobs/bulk/delete', payload),
      'Error deleting jobs');
  },
  
  getJobHistory: async (id: number): Promise<SalaryHistoryEntry[]> => {
    return handleRequest(apiClient.get<SalaryHistoryEntry[]>(`/jobs/${id}/history`),
      'Error loading salary history');
  },

  getCompanyHistory: async (company: string): Promise<SalaryHistoryEntry[]> => {
    return handleRequest(apiClient.get<SalaryHistoryEntry[]>('/jobs/history/by-company', { params: { company } }),
      'Error loading company salary history');
  },

  deleteSalaryHistoryEntry: async (recordId: string): Promise<{ deleted: number }> => {
    return handleRequest(apiClient.delete<{ deleted: number }>(`/jobs/history/${recordId}`),
      'Error deleting salary history entry');
  },

  getSystemTimezone: async (): Promise<{ offset_minutes: number }> => {
    if (!timezonePromise) {
      timezonePromise = handleRequest(apiClient.get<{ offset_minutes: number }>('/system/timezone'),
        'Error getting system timezone');
    }
    return timezonePromise;
  },
};
