import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
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
  ai_enriched: boolean | null;
  // Other fields
  required_technologies: string | null;
  optional_technologies: string | null;
  client: string | null;
  comments: string | null;
  cv_match_percentage: number | null;
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
}

export const jobsApi = {
  getJobs: async (params: JobListParams = {}): Promise<JobListResponse> => {
    const response = await apiClient.get<JobListResponse>('/jobs', { params });
    return response.data;
  },

  getJob: async (id: number): Promise<Job> => {
    const response = await apiClient.get<Job>(`/jobs/${id}`);
    return response.data;
  },

  updateJob: async (id: number, data: Partial<Job>): Promise<Job> => {
    const response = await apiClient.patch<Job>(`/jobs/${id}`, data);
    return response.data;
  },
};
