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
  duplicated_id: number | string | null;
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
  ai_enrich_error: string | null;
  modality: string[] | null;
  hybrid_info: string | null;
  synonyms?: string[] | null;
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
  error?: string;
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
  modality?: string[];
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
  duplicated?: boolean;
  sql_filter?: string;
  ids?: number[];
  created_after?: string;
  // Configuration behaviour saved with the filter set, not sent to the jobs API:
  // `true` selects every matching job when the configuration loads, `null`/absent leaves it unselected.
  auto_select_all?: boolean | null;
  // `true` expands the filters panel when the configuration loads, `null`/absent collapses it.
  filter_expanded?: boolean | null;
}

export interface WatcherStats {
  total: number;
  new_items: number;
  removed_items: number;
}

export interface SalaryHistoryEntry {
  id: string;
  job_id: number;
  company_raw: string;
  company_normalized: string;
  title: string;
  salary: string;
  recorded_at: string;
  source: string;
}
