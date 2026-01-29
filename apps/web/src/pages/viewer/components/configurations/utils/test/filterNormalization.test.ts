import { describe, it, expect } from 'vitest';
import { normalizeFilters } from '../filterNormalization';
import type { JobListParams } from '../../../../api/jobs';

describe('normalizeFilters', () => {
  it('should preserve existing filter values', () => {
    const filters: JobListParams = { page: 1, size: 10, search: 'test' };
    const result = normalizeFilters(filters);
    expect(result.page).toBe(1);
    expect(result.size).toBe(10);
    expect(result.search).toBe('test');
  });

  it('should add undefined for missing resettable filters', () => {
    const filters: JobListParams = { page: 1 };
    const result = normalizeFilters(filters);
    expect(result.days_old).toBeUndefined();
    expect(result.salary).toBeUndefined();
    expect(result.sql_filter).toBeUndefined();
  });

  it('should not override existing boolean filters', () => {
    const filters: JobListParams = { flagged: true, like: false };
    const result = normalizeFilters(filters);
    expect(result.flagged).toBe(true);
    expect(result.like).toBe(false);
  });
});
