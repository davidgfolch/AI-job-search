export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  url: string;
  source: 'linkedin' | 'infojobs' | 'glassdoor' | 'tecnoempleo' | string;
  salary?: string;
  salary_min?: number;
  salary_max?: number;
  required_technologies?: string[];
  job_type?: 'full_time' | 'part_time' | 'contract' | 'remote' | string;
  experience_level?: 'junior' | 'mid' | 'senior' | 'lead' | string;
  posted_date: string;
  scraped_date: string;
  state: JobState;
  comments?: string;
  ai_enriched: boolean;
  ai_summary?: string;
  ai_skills?: string[];
  ai_salary_estimate?: string;
  created_at: string;
  updated_at: string;
}

export type JobState = 
  | 'new'
  | 'seen'
  | 'applied'
  | 'interview_scheduled'
  | 'interviewed'
  | 'rejected'
  | 'offer_received'
  | 'accepted'
  | 'declined'
  | 'ignored'
  | 'discarded'
  | 'closed';

export interface JobFilters {
  search?: string;
  company?: string;
  location?: string;
  source?: string[];
  state?: JobState[];
  salary_min?: number;
  salary_max?: number;
  job_type?: string[];
  experience_level?: string[];
  required_technologies?: string[];
  posted_after?: string;
  posted_before?: string;
  ai_enriched?: boolean;
  limit?: number;
  offset?: number;
  sort_by?: 'posted_date' | 'scraped_date' | 'salary_max' | 'title' | 'company';
  sort_order?: 'asc' | 'desc';
}

export interface JobsResponse {
  jobs: Job[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface JobUpdate {
  state?: JobState;
  comments?: string;
}

export interface JobStats {
  total_jobs: number;
  by_state: Record<JobState, number>;
  by_source: Record<string, number>;
  by_technology: Record<string, number>;
  avg_salary?: number;
  salary_range?: {
    min: number;
    max: number;
  };
  latest_scrape: string;
  ai_enriched_count: number;
}

export interface CleanupCriteria {
  older_than_days?: number;
  states_to_delete?: JobState[];
  sources_to_delete?: string[];
  ignore_patterns?: string[];
}

export interface CleanupResult {
  deleted_count: number;
  ignored_count: number;
  message: string;
}