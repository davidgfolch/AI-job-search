// src/api/client.ts

import axios, { AxiosResponse } from 'axios';
import { 
  Job, 
  JobFilters, 
  JobsResponse, 
  JobUpdate, 
  JobStats, 
  CleanupCriteria, 
  CleanupResult 
} from '@/types/job';

// Base API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class JobApi {
  // Get jobs with filtering and pagination
  static async getJobs(filters: JobFilters = {}): Promise<JobsResponse> {
    const params = new URLSearchParams();
    
    // Add filters as query parameters
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v.toString()));
        } else {
          params.append(key, value.toString());
        }
      }
    });

    const response: AxiosResponse<JobsResponse> = await apiClient.get(
      `/api/jobs?${params.toString()}`
    );
    return response.data;
  }

  // Get single job by ID
  static async getJob(id: number): Promise<Job> {
    const response: AxiosResponse<Job> = await apiClient.get(`/api/jobs/${id}`);
    return response.data;
  }

  // Update job (state, comments, etc.)
  static async updateJob(id: number, updates: JobUpdate): Promise<Job> {
    const response: AxiosResponse<Job> = await apiClient.patch(
      `/api/jobs/${id}`, 
      updates
    );
    return response.data;
  }

  // Bulk update multiple jobs
  static async bulkUpdateJobs(ids: number[], updates: JobUpdate): Promise<{ updated_count: number }> {
    const response: AxiosResponse<{ updated_count: number }> = await apiClient.patch(
      '/api/jobs/bulk',
      { ids, updates }
    );
    return response.data;
  }

  // Delete job
  static async deleteJob(id: number): Promise<void> {
    await apiClient.delete(`/api/jobs/${id}`);
  }

  // Bulk delete jobs
  static async bulkDeleteJobs(ids: number[]): Promise<{ deleted_count: number }> {
    const response: AxiosResponse<{ deleted_count: number }> = await apiClient.delete(
      '/api/jobs/bulk',
      { data: { ids } }
    );
    return response.data;
  }

  // Get job statistics
  static async getStats(): Promise<JobStats> {
    const response: AxiosResponse<JobStats> = await apiClient.get('/api/stats');
    return response.data;
  }

  // Clean up old jobs based on criteria
  static async cleanupJobs(criteria: CleanupCriteria): Promise<CleanupResult> {
    const response: AxiosResponse<CleanupResult> = await apiClient.post(
      '/api/cleanup',
      criteria
    );
    return response.data;
  }

  // Get available filter options (companies, technologies, etc.)
  static async getFilterOptions(): Promise<{
    companies: string[];
    locations: string[];
    sources: string[];
    technologies: string[];
    job_types: string[];
    experience_levels: string[];
  }> {
    const response = await apiClient.get('/api/filters/options');
    return response.data;
  }

  // Trigger AI enrichment for specific jobs
  static async enrichJobs(ids: number[]): Promise<{ queued_count: number }> {
    const response: AxiosResponse<{ queued_count: number }> = await apiClient.post(
      '/api/enrich',
      { ids }
    );
    return response.data;
  }

  // Get scraper status and controls
  static async getScraperStatus(): Promise<{
    linkedin: { running: boolean; last_run: string; jobs_found: number };
    infojobs: { running: boolean; last_run: string; jobs_found: number };
    glassdoor: { running: boolean; last_run: string; jobs_found: number };
    tecnoempleo: { running: boolean; last_run: string; jobs_found: number };
  }> {
    const response = await apiClient.get('/api/scrapers/status');
    return response.data;
  }

  // Start/stop scrapers
  static async controlScraper(
    scraper: string, 
    action: 'start' | 'stop'
  ): Promise<{ status: string; message: string }> {
    const response = await apiClient.post(`/api/scrapers/${scraper}/${action}`);
    return response.data;
  }
}

export default JobApi;