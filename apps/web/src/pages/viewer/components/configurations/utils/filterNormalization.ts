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

/** The defined entries of a filter set, ordered by key so two objects can be compared without depending on
 * insertion order. Keys explicitly set to `undefined` are dropped, because the API drops them too and a filter
 * that was never set is the same request as one that was cleared. */
const comparableEntries = (filters: JobListParams): [string, unknown][] =>
  Object.entries(filters)
    .filter(([, value]) => value !== undefined)
    .sort(([left], [right]) => left.localeCompare(right)) as [string, unknown][];

/** Whether two filter sets produce the same query key.
 *
 * The job list query is keyed by its filters, so an unchanged filter set resolves to the already cached query and
 * TanStack Query does not refetch it while it is fresh. Array values are compared as ordered, which is how the
 * query key hash serializes them (`modality: ['a', 'b']` and `['b', 'a']` are different requests). */
export const isSameFilterSet = (left: JobListParams, right: JobListParams): boolean => {
  const leftEntries = comparableEntries(left);
  const rightEntries = comparableEntries(right);
  return leftEntries.length === rightEntries.length
    && leftEntries.every(([key, value], index) => key === rightEntries[index][0] && JSON.stringify(value) === JSON.stringify(rightEntries[index][1]));
};
