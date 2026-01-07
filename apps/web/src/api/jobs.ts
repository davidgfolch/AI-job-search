import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: (params) => {
    const searchParams = new URLSearchParams();
    Object.keys(params).forEach(key => {
      const value = params[key];
      if (value === undefined || value === null) return;
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, v.toString()));
      } else {
        searchParams.append(key, value.toString());
      }
    });
    return searchParams.toString();
  },
});

export interface Job {
  id: number;
  title: string | null;
  company: string | null;
  location: string | null;
  salary: string | null;
  url: string | null;
  markdown: string | null;
  web_page: string | null;
  created: string | null;
  modified: string | null;
  // Boolean fields
  flagged: boolean | null;
  like: boolean | null;
  ignored: boolean | null;
  seen: boolean | null;
  applied: boolean | null;
  discarded: boolean | null;
  closed: boolean | null;
  interview_rh: boolean | null;
  interview: boolean | null;
  interview_tech: boolean | null;
  interview_technical_test: boolean | null;
  interview_technical_test_done: boolean | null;
  ai_enriched: boolean | null;
  easy_apply: boolean | null;
  // Other fields
  required_technologies: string | null;
  optional_technologies: string | null;
  client: string | null;
  comments: string | null;
  cv_match_percentage: number | null;
}

export interface AppliedCompanyJob {
  id: number;
  created: string | null;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  size: number;
}

export interface JobListParams {
  page?: number;
  size?: number;
  search?: string;
  status?: string;
  not_status?: string;
  days_old?: number;
  salary?: string;
  order?: string;
  // Boolean field filters
  flagged?: boolean;
  like?: boolean;
  ignored?: boolean;
  seen?: boolean;
  applied?: boolean;
  discarded?: boolean;
  closed?: boolean;
  interview_rh?: boolean;
  interview?: boolean;
  interview_tech?: boolean;
  interview_technical_test?: boolean;
  interview_technical_test_done?: boolean;
  ai_enriched?: boolean;
  easy_apply?: boolean;
  sql_filter?: string;
  ids?: number[];
}

const handleRequest = async <T>(request: Promise<{ data: T }>, errorMessage: string): Promise<T> => {
  try {
    const response = await request;
    return response.data;
  } catch (error) {
    throw new Error(`${errorMessage}: ${error instanceof Error ? error.message : String(error)}`);
  }
};

export const jobsApi = {
  getJobs: async (params: JobListParams = {}): Promise<JobListResponse> => {
    return handleRequest(apiClient.get<JobListResponse>('/jobs', { params }),
      'Error loading jobs');
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
};
