import { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/ViewerApi';
import { DEFAULT_FILTERS } from '../constants';

export const useJobsData = () => {
    const [filters, setFilters] = useState<JobListParams>(DEFAULT_FILTERS);
    const [allJobs, setAllJobs] = useState<Job[]>([]);
    const [isLoadingMore, setIsLoadingMore] = useState(false);

    const queryClient = useQueryClient();

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => jobsApi.getJobs(filters),
    });

    const hardRefresh = useCallback(async () => {
        await queryClient.resetQueries({ queryKey: ['jobs'] });
    }, [queryClient]);

    const handleLoadMore = useCallback(() => {
        if (!isLoadingMore && !isLoading && allJobs.length < (data?.total || 0)) {
            setIsLoadingMore(true);
            setFilters(prev => ({ ...prev, page: (prev.page || 1) + 1 }));
        }
    }, [isLoadingMore, isLoading, allJobs.length, data?.total]);

    return {
        filters,
        setFilters,
        allJobs,
        setAllJobs,
        isLoadingMore,
        data,
        isLoading,
        error,
        handleLoadMore,
        setIsLoadingMore,
        refetch,
        hardRefresh
    };
};
