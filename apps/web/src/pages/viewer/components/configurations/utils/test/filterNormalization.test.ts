import { describe, it, expect } from 'vitest';
import { normalizeFilters, isSameFilterSet } from '../filterNormalization';
import type { JobListParams } from '../../../../api/ViewerApi';

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

  it('should reset auto_select_all when the configuration does not store it', () => {
    const result = normalizeFilters({ page: 1 });
    expect(result).toHaveProperty('auto_select_all', undefined);
  });

  it('should keep auto_select_all set to null, which means explicitly unselected', () => {
    const result = normalizeFilters({ page: 1, auto_select_all: null });
    expect(result.auto_select_all).toBeNull();
  });

  it('should reset filter_expanded when the configuration does not store it', () => {
    const result = normalizeFilters({ page: 1 });
    expect(result).toHaveProperty('filter_expanded', undefined);
  });

  it('should keep filter_expanded set to null, which means explicitly collapsed', () => {
    const result = normalizeFilters({ page: 1, filter_expanded: null });
    expect(result.filter_expanded).toBeNull();
  });

  it('should keep filter_expanded set to true', () => {
    const result = normalizeFilters({ page: 1, filter_expanded: true });
    expect(result.filter_expanded).toBe(true);
  });

  it('should not override existing boolean filters', () => {
    const filters: JobListParams = { flagged: true, like: false };
    const result = normalizeFilters(filters);
    expect(result.flagged).toBe(true);
    expect(result.like).toBe(false);
  });
});

describe('isSameFilterSet', () => {
  it('reports identical filter sets regardless of key order', () => {
    expect(isSameFilterSet({ page: 1, search: 'jvm', ai_enriched: true }, { ai_enriched: true, search: 'jvm', page: 1 })).toBe(true);
  });

  it('treats a key set to undefined as absent, since the API drops it', () => {
    expect(isSameFilterSet({ page: 1, sql_filter: undefined }, { page: 1 })).toBe(true);
  });

  it.each([
    ['different search', { page: 1, search: 'jvm' }, { page: 1, search: 'python' }],
    ['different boolean', { page: 1, ai_enriched: true }, { page: 1, ai_enriched: false }],
    ['different page', { page: 1, search: 'jvm' }, { page: 3, search: 'jvm' }],
    ['extra key', { page: 1, search: 'jvm' }, { page: 1, search: 'jvm', size: 20 }],
  ])('reports different filter sets: %s', (_label, left, right) => {
    expect(isSameFilterSet(left as JobListParams, right as JobListParams)).toBe(false);
  });

  it('compares array values in order, like the query key hash does', () => {
    expect(isSameFilterSet({ modality: ['remote', 'hybrid'] }, { modality: ['hybrid', 'remote'] })).toBe(false);
    expect(isSameFilterSet({ modality: ['remote', 'hybrid'] }, { modality: ['remote', 'hybrid'] })).toBe(true);
  });
});
