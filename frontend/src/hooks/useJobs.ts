// src/hooks/useJobs.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { JobApi } from '@/api/client';
import { JobFilters, JobUpdate, CleanupCriteria } from '@/types/job';
import { toast } from 'react-hot-toast';

// Query Keys
export const jobKeys = {
  all: ['jobs'] as const,
  lists: () => [...jobKeys.all, 'list'] as const,
  list: (filters: JobFilters) => [...jobKeys.lists(), filters] as const,
  details: () => [...jobKeys.all, 'detail'] as const,
  detail: (id: number) => [...jobKeys.details(), id] as const,
  stats: () => [...jobKeys.all, 'stats'] as const,
  filterOptions: () => [...jobKeys.all, 'filter-options'] as const,
  scraperStatus: () => [...jobKeys.all, 'scraper-status'] as const,
};

// Hook for fetching jobs with filters
export function useJobs(filters: JobFilters = {}) {
  return useQuery({
    queryKey: jobKeys.list(filters),
    queryFn: () => JobApi.getJobs(filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
  });
}

// Hook for fetching single job
export function useJob(id: number) {
  return useQuery({
    queryKey: jobKeys.detail(id),
    queryFn: () => JobApi.getJob(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  });
}

// Hook for job statistics
export function useJobStats() {
  return useQuery({
    queryKey: jobKeys.stats(),
    queryFn: () => JobApi.getStats(),
    staleTime: 1000 * 60 * 2, // 2 minutes
    refetchInterval: 1000 * 60 * 5, // Auto-refresh every 5 minutes
  });
}

// Hook for filter options
export function useFilterOptions() {
  return useQuery({
    queryKey: jobKeys.filterOptions(),
    queryFn: () => JobApi.getFilterOptions(),
    staleTime: 1000 * 60 * 15, // 15 minutes
  });
}

// Hook for scraper status
export function useScraperStatus() {
  return useQuery({
    queryKey: jobKeys.scraperStatus(),
    queryFn: () => JobApi.getScraperStatus(),
    refetchInterval: 1000 * 30, // Refresh every 30 seconds
    staleTime: 1000 * 15, // 15 seconds
  });
}

// Mutation for updating single job
export function useUpdateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: JobUpdate }) =>
      JobApi.updateJob(id, updates),
    onSuccess: (updatedJob, { id }) => {
      // Update the job in cache
      queryClient.setQueryData(jobKeys.detail(id), updatedJob);
      
      // Invalidate job lists to refresh them
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast.success('Job updated successfully');
    },
    onError: (error) => {
      console.error('Failed to update job:', error);
      toast.error('Failed to update job');
    },
  });
}

// Mutation for bulk updating jobs
export function useBulkUpdateJobs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ids, updates }: { ids: number[]; updates: JobUpdate }) =>
      JobApi.bulkUpdateJobs(ids, updates),
    onSuccess: (result) => {
      // Invalidate all job-related queries
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
      toast.success(`${result.updated_count} jobs updated successfully`);
    },
    onError: (error) => {
      console.error('Failed to bulk update jobs:', error);
      toast.error('Failed to update jobs');
    },
  });
}

// Mutation for deleting job
export function useDeleteJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => JobApi.deleteJob(id),
    onSuccess: (_, id) => {
      // Remove job from cache
      queryClient.removeQueries({ queryKey: jobKeys.detail(id) });
      
      // Invalidate lists and stats
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      
      toast.success('Job deleted successfully');
    },
    onError: (error) => {
      console.error('Failed to delete job:', error);
      toast.error('Failed to delete job');
    },
  });
}

// Mutation for bulk deleting jobs
export function useBulkDeleteJobs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => JobApi.bulkDeleteJobs(ids),
    onSuccess: (result) => {
      // Invalidate all job-related queries
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
      toast.success(`${result.deleted_count} jobs deleted successfully`);
    },
    onError: (error) => {
      console.error('Failed to bulk delete jobs:', error);
      toast.error('Failed to delete jobs');
    },
  });
}

// Mutation for cleaning up jobs
export function useCleanupJobs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (criteria: CleanupCriteria) => JobApi.cleanupJobs(criteria),
    onSuccess: (result) => {
      // Invalidate all job-related queries
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
      toast.success(result.message);
    },
    onError: (error) => {
      console.error('Failed to cleanup jobs:', error);
      toast.error('Failed to cleanup jobs');
    },
  });
}

// Mutation for AI enrichment
export function useEnrichJobs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ids: number[]) => JobApi.enrichJobs(ids),
    onSuccess: (result) => {
      // Invalidate job lists to show updated enrichment status
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.stats() });
      toast.success(`${result.queued_count} jobs queued for AI enrichment`);
    },
    onError: (error) => {
      console.error('Failed to enrich jobs:', error);
      toast.error('Failed to queue jobs for enrichment');
    },
  });
}

// Mutation for controlling scrapers
export function useControlScraper() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ scraper, action }: { scraper: string; action: 'start' | 'stop' }) =>
      JobApi.controlScraper(scraper, action),
    onSuccess: (result, { scraper, action }) => {
      // Invalidate scraper status
      queryClient.invalidateQueries({ queryKey: jobKeys.scraperStatus() });
      toast.success(`${scraper} scraper ${action}ed: ${result.message}`);
    },
    onError: (error, { scraper, action }) => {
      console.error(`Failed to ${action} ${scraper} scraper:`, error);
      toast.error(`Failed to ${action} ${scraper} scraper`);
    },
  });
}