import type { JobListParams } from "../api/jobs";

export const DEFAULT_FILTERS: JobListParams = {
  page: 1,
  size: 20,
  search: "",
  order: "created desc",
  ai_enriched: true,
  ignored: false,
  seen: false,
  applied: false,
  discarded: false,
  closed: false,
};

export const STATE_FIELDS = [
  'flagged', 'like', 'ignored', 'seen', 'applied', 'discarded', 'closed',
  'interview_rh', 'interview', 'interview_tech', 'interview_technical_test',
  'interview_technical_test_done', 'ai_enriched', 'easy_apply'
]
