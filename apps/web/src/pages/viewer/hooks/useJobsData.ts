import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/ViewerApi';
import { DEFAULT_FILTERS } from '../constants';

export const useJobsData = () => {
    const [searchParams] = useSearchParams();

    const getInitialFilters = (): JobListParams => {
        const idsParam = searchParams.get('ids');
        if (idsParam) {
            const ids = idsParam.split(',').map(n => parseInt(n, 10)).filter(n => !isNaN(n));
            if (ids.length > 0) {
                return {
                    ...DEFAULT_FILTERS,
                    ids,
                    // When showing specific IDs, disable default filters to ensure they are visible
                    ai_enriched: undefined,
                    ignored: undefined,
                    seen: undefined,
                    applied: undefined,
                    discarded: undefined,
                    closed: undefined,
                    page: 1,
                };
            }
        }
        return DEFAULT_FILTERS;
    };

    const [filters, setFilters] = useState<JobListParams>(getInitialFilters);
    const [allJobs, setAllJobs] = useState<Job[]>([]);
    const [isLoadingMore, setIsLoadingMore] = useState(false);

    const queryClient = useQueryClient();

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => jobsApi.getJobs(filters),
    });

    const hardRefresh = useCallback(async () => {
        await Promise.all([
            queryClient.resetQueries({ queryKey: ['jobs'] }),
            queryClient.resetQueries({ queryKey: ['jobUpdates'] })
        ]);
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
