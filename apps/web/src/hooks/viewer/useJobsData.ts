import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../../api/jobs';
import { DEFAULT_FILTERS } from '../contants';

export const useJobsData = () => {
    const [filters, setFilters] = useState<JobListParams>(DEFAULT_FILTERS);
    const [allJobs, setAllJobs] = useState<Job[]>([]);
    const [isLoadingMore, setIsLoadingMore] = useState(false);

    const { data, isLoading, error } = useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => jobsApi.getJobs(filters),
    });

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
        setIsLoadingMore
    };
};
