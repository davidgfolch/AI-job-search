import type { JobListParams } from '../../../api/ViewerApi';
import { BOOLEAN_FILTER_KEYS } from '../../../constants';

const RESETTABLE_FILTERS: (keyof JobListParams)[] = [
  'days_old',
  'search',
  'salary',
  'sql_filter',
  ...BOOLEAN_FILTER_KEYS,
];

export const normalizeFilters = (filters: JobListParams): JobListParams => ({
  ...filters,
  ...Object.fromEntries(
    RESETTABLE_FILTERS
      .filter(key => !(key in filters))
      .map(key => [key, undefined])
  ),
});
