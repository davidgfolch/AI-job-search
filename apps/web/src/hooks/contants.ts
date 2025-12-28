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

export const STATE_FIELDS = [  //see BOOLEAN_FILTERS
  "ignored",
  "seen",
  "applied",
  "discarded",
  "closed",
  "flagged",
  "like",
  "ai_enriched",
];
