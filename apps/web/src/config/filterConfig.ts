import type { JobListParams } from '../api/jobs';

/**
 * Configuration for a boolean filter item
 */
export interface BooleanFilterConfig {
    key: keyof JobListParams;
    label: string;
}

/**
 * Complete list of all boolean filter configurations
 * This is the single source of truth for all boolean filters across the application
 */
export const BOOLEAN_FILTERS: BooleanFilterConfig[] = [
    // Status Flags
    { key: 'flagged', label: 'Flagged' },
    { key: 'like', label: 'Like' },
    { key: 'ignored', label: 'Ignored' },
    { key: 'seen', label: 'Seen' },
    // Application Status
    { key: 'applied', label: 'Applied' },
    { key: 'discarded', label: 'Discarded' },
    { key: 'closed', label: 'Closed' },
    // Interview Process
    { key: 'interview_rh', label: 'Interview (RH)' },
    { key: 'interview', label: 'Interview' },
    { key: 'interview_tech', label: 'Interview (Tech)' },
    { key: 'interview_technical_test', label: 'Technical Test' },
    { key: 'interview_technical_test_done', label: 'Technical Test Done' },
    // Other
    { key: 'ai_enriched', label: 'AI Enriched' },
    { key: 'easy_apply', label: 'Easy Apply' },
];

/**
 * Array of just the filter keys for type-safe iteration
 */
export const BOOLEAN_FILTER_KEYS: (keyof JobListParams)[] = BOOLEAN_FILTERS.map(f => f.key);
